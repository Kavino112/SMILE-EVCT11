"""Data coordinator for AlphaESS Wallbox Bridge."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlphaESSPortalApi, AuthenticationError, PortalConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlphaESSWallboxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch the current wallbox state from the AlphaESS customer portal."""

    def __init__(self, hass: HomeAssistant, api: AlphaESSPortalApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=2),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_wallbox_data()
        except (AuthenticationError, PortalConnectionError) as err:
            _LOGGER.warning("AlphaESS wallbox refresh failed during %s with status %s", err.step, getattr(err, "status", "authorization"))
            raise UpdateFailed(f"AlphaESS wallbox refresh failed during {err.step}") from err
