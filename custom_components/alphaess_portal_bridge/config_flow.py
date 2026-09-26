"""Config flow for AlphaESS Portal Bridge."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import AlphaESSPortalApi, AuthenticationError, PortalConnectionError
from .const import (
    CONF_PASSWORD,
    CONF_SYSTEM_SERIAL,
    CONF_USERNAME,
    CONF_WALLBOX_SERIAL,
    DOMAIN,
)


class AlphaESSPortalBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the bridge through the current AlphaESS portal session API."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] | None = None
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SYSTEM_SERIAL])
            self._abort_if_unique_id_configured()
            api = AlphaESSPortalApi(self.hass, user_input)
            try:
                await api.async_validate_login()
            except AuthenticationError as err:
                errors["base"] = (
                    "session_rejected"
                    if err.step == "session validation"
                    else "system_access_denied"
                    if err.step == "system check"
                    else "invalid_auth"
                )
            except PortalConnectionError as err:
                if err.status is None:
                    errors["base"] = "cannot_connect"
                else:
                    errors["base"] = "portal_status"
                    description_placeholders = {
                        "step": err.step,
                        "status": str(err.status),
                    }
            else:
                return self.async_create_entry(
                    title=f"AlphaESS Wallbox {user_input[CONF_SYSTEM_SERIAL]}",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SYSTEM_SERIAL): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add the wallbox serial to an existing portal connection."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            wallbox_serial = user_input[CONF_WALLBOX_SERIAL].strip().upper()
            self.hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_WALLBOX_SERIAL: wallbox_serial},
                title=f"AlphaESS Wallbox {entry.data[CONF_SYSTEM_SERIAL]}",
            )
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {vol.Required(CONF_WALLBOX_SERIAL): str}
            ),
        )
