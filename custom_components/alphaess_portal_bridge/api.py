"""Authenticated, session-based access to the AlphaESS customer portal."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import re
import time
from typing import Any

import aiohttp
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_PASSWORD,
    CONF_SYSTEM_SERIAL,
    CONF_WALLBOX_SERIAL,
    CONF_USERNAME,
    API_URL,
)

PORTAL_HEADERS = {
    "Tenant": "alphaess",
    "Client-End": "Web",
    "Client-Name": "Portal",
}


class AuthenticationError(Exception):
    """The portal did not authorize the current session."""

    def __init__(self, step: str = "login") -> None:
        self.step = step
        super().__init__(f"Portal authorization failed during {step}")


class PortalConnectionError(Exception):
    """The portal could not be reached."""

    def __init__(self, status: int | None = None, step: str = "connection") -> None:
        self.status = status
        self.step = step
        super().__init__(f"Portal request failed during {step}: {status}")


class AlphaESSPortalApi:
    """Keep an AlphaESS customer-portal session in memory."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self._session = async_get_clientsession(hass)
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._system_serial = config[CONF_SYSTEM_SERIAL]
        self._wallbox_serial = config.get(CONF_WALLBOX_SERIAL)
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at = 0.0
        self._api_url = API_URL

    async def async_validate_login(self) -> None:
        """Validate the system access with the newly created portal session."""
        await self._async_get(
            f"/internal/v1/ess/{self._system_serial}",
            params={"components": "basic,g1T"},
            step="system check",
        )

    async def async_get_wallbox_data(self) -> dict[str, Any]:
        """Read the system and its attached wallbox without sending commands."""
        system = await self._async_get(
            f"/internal/v1/ess/{self._system_serial}",
            params={"components": "basic,g1T"},
            step="system check",
        )
        # The customer portal keeps the charge strategy in the full system
        # document, while the compact component request only contains live
        # readings.  Keep the result private and use it solely to find the
        # wallbox configuration; it is never logged or exposed wholesale.
        try:
            configuration = await self._async_get(
                f"/internal/v1/ess/{self._system_serial}",
                step="wallbox configuration",
            )
        except PortalConnectionError:
            configuration = {}
        wallbox_serial = self._wallbox_serial or self._find_wallbox_serial(system)
        wallbox_status = self._find_wallbox_data(system, wallbox_serial)
        wallbox_status_source = "system"
        if wallbox_serial:
            try:
                wallbox_status = await self._async_get(
                    f"/internal/v1/ev-charger/{wallbox_serial}/real-status",
                    step="wallbox status",
                )
                wallbox_status_source = "real_status"
            except PortalConnectionError as err:
                if err.status != 409:
                    raise
        return {
            "system": system,
            "configuration": configuration,
            "wallbox_serial": wallbox_serial,
            "wallbox_status": wallbox_status,
            "wallbox_status_source": wallbox_status_source,
        }

    async def async_control_wallbox(self, control: str) -> None:
        """Send a guarded start or stop request to the wallbox."""
        if control not in {"START", "STOP"}:
            raise ValueError("Unsupported wallbox control")
        wallbox_serial = self._wallbox_serial
        if not wallbox_serial:
            raise PortalConnectionError(step="wallbox control")
        status_data = await self._async_get(
            f"/internal/v1/ev-charger/{wallbox_serial}/real-status",
            step="wallbox control status",
        )
        status = status_data.get("status") if isinstance(status_data, dict) else None
        allowed = (
            {"PendingStart", "ChargingStopped", "CharingStopped"}
            if control == "START"
            else {"Charging"}
        )
        if status not in allowed:
            raise PortalConnectionError(step="wallbox control blocked")
        await self._async_authenticated_post(
            f"/internal/v1/ev-charger/{wallbox_serial}/events",
            {"control": control},
            step="wallbox control",
        )

    async def async_update_wallbox_settings(
        self, *, charge_mode: int | None = None, charge_current: int | None = None
    ) -> None:
        """Update only the portal's wallbox settings, retaining all other data."""
        if charge_mode is not None and charge_mode not in {0, 1, 2, 3, 4}:
            raise ValueError("Unsupported charge mode")
        if charge_current is not None and not 6 <= charge_current <= 16:
            raise ValueError("Charge current must be between 6 and 16 A")
        configuration = await self._async_get(
            f"/internal/v1/ess/{self._system_serial}", step="wallbox settings"
        )
        wallbox = self._find_wallbox_data(configuration, self._wallbox_serial)
        settings = wallbox.get("g1T") if isinstance(wallbox.get("g1T"), dict) else None
        if not settings:
            raise PortalConnectionError(step="wallbox settings")
        if charge_mode is not None:
            settings["chargeMode"] = charge_mode
        if charge_current is not None:
            settings["chargeCurrent"] = charge_current
        await self._async_authenticated_patch(
            f"/internal/v1/ess/{self._system_serial}", configuration, step="wallbox settings"
        )

    @staticmethod
    def _find_wallbox_serial(value: Any) -> str | None:
        """Find an AlphaESS wallbox serial number in the system response."""
        if isinstance(value, str) and re.fullmatch(r"ALP\d{6,}", value):
            return value
        if isinstance(value, dict):
            for item in value.values():
                serial = AlphaESSPortalApi._find_wallbox_serial(item)
                if serial:
                    return serial
        if isinstance(value, list):
            for item in value:
                serial = AlphaESSPortalApi._find_wallbox_serial(item)
                if serial:
                    return serial
        return None

    @staticmethod
    def _find_wallbox_data(value: Any, serial: str | None) -> dict[str, Any]:
        """Return the closest system object containing the wallbox serial."""
        if not serial:
            return {}
        if isinstance(value, dict):
            if any(item == serial for item in value.values()):
                return value
            for item in value.values():
                found = AlphaESSPortalApi._find_wallbox_data(item, serial)
                if found:
                    return found
        if isinstance(value, list):
            for item in value:
                found = AlphaESSPortalApi._find_wallbox_data(item, serial)
                if found:
                    return found
        return {}

    async def _async_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at:
            return self._token

        if self._refresh_token:
            payload = await self._async_post(
                f"{self._api_url}/users-center/sessions/refresh",
                {"refreshToken": self._refresh_token},
            )
        else:
            await self._async_select_region()
            payload = await self._async_post(
                f"{self._api_url}/users-center/sessions",
                {
                    "email": self._username.strip(),
                    "password": self._encrypt_password(),
                    "type": "password",
                },
            )

        # The portal has returned both a direct session document and a
        # data-wrapped session document during its rollout.  Accept either
        # shape, but never persist or log the credential material here.
        session = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        token = session.get("token") or session.get("accessToken")
        refresh_token = session.get("refreshToken")
        if not token:
            raise AuthenticationError
        token_type = session.get("tokenType", "Bearer")
        self._token = token if token.startswith(f"{token_type} ") else f"{token_type} {token}"
        self._refresh_token = refresh_token if isinstance(refresh_token, str) else None
        self._expires_at = time.monotonic() + max(
            60, int(session.get("expiresIn", 300)) - 30
        )
        return token

    async def _async_select_region(self) -> None:
        """Resolve the regional API endpoint the customer portal uses."""
        try:
            async with self._session.get(
                f"{API_URL}/users-center/users/region",
                params={"usernameOrEmail": self._username.strip()},
                headers=PORTAL_HEADERS,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (400, 401, 403):
                    raise AuthenticationError
                if response.status != 200:
                    raise PortalConnectionError(response.status, "region lookup")
                region = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PortalConnectionError from err

        endpoint = region.get("endPoint") if isinstance(region, dict) else None
        if isinstance(endpoint, str) and endpoint.startswith("https://"):
            self._api_url = endpoint.rstrip("/")

    def _encrypt_password(self) -> str:
        """Apply the AES-CBC password transformation used by the portal UI."""
        account = self._username.strip().encode()
        key = hashlib.sha256(account).digest()
        iv = hashlib.md5(account, usedforsecurity=False).digest()
        padder = PKCS7(algorithms.AES.block_size).padder()
        padded = padder.update(self._password.strip().encode()) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(ciphertext).decode()

    async def _async_post(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.post(
                url,
                json=data,
                headers=PORTAL_HEADERS,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (400, 401, 403):
                    raise AuthenticationError
                if response.status not in (200, 201):
                    raise PortalConnectionError(response.status, "login")
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PortalConnectionError from err

    async def _async_authenticated_post(
        self, path: str, data: dict[str, Any], *, step: str
    ) -> None:
        """Post a wallbox command using the current portal session."""
        await self._async_token()
        try:
            async with self._session.post(
                f"{self._api_url}{path}",
                json=data,
                headers={**PORTAL_HEADERS, "Authorization": self._token},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError(step)
                if response.status not in (200, 201, 204):
                    raise PortalConnectionError(response.status, step)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PortalConnectionError from err

    async def _async_authenticated_patch(
        self, path: str, data: dict[str, Any], *, step: str
    ) -> None:
        """Patch the current portal configuration with an authenticated session."""
        await self._async_token()
        try:
            async with self._session.patch(
                f"{self._api_url}{path}", json=data,
                headers={**PORTAL_HEADERS, "Authorization": self._token},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError(step)
                if response.status not in (200, 201, 204):
                    raise PortalConnectionError(response.status, step)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PortalConnectionError from err

    async def _async_get(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        step: str,
    ) -> dict[str, Any]:
        token = await self._async_token()
        try:
            async with self._session.get(
                f"{self._api_url}{path}",
                params=params,
                headers={**PORTAL_HEADERS, "Authorization": self._token},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError(step)
                if response.status != 200:
                    raise PortalConnectionError(response.status, step)
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PortalConnectionError from err
