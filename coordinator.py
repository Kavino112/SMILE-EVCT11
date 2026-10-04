"""Data coordinator for AlphaESS Wallbox Bridge."""
# ---------------------------------------------------------------------------
# Community-Build fuer https://www.storion4you.de/
# G2T-Erweiterung fuer SMILE-G3-EVCT11/S: Kavino
# Basierend auf dem Ausgangsprojekt wfa001/SMILE-EVCT11.
# Details und Attribution: siehe NOTICE.md im Paket.
# ---------------------------------------------------------------------------
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlphaESSPortalApi, AuthenticationError, PortalConnectionError
from .const import DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN, UPDATE_INTERVAL_OPTIONS

_LOGGER = logging.getLogger(__name__)


class AlphaESSWallboxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch the current wallbox state from the AlphaESS customer portal."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: AlphaESSPortalApi,
        update_interval_seconds: int = DEFAULT_UPDATE_INTERVAL_SECONDS,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=(
                    update_interval_seconds
                    if update_interval_seconds in UPDATE_INTERVAL_OPTIONS
                    else DEFAULT_UPDATE_INTERVAL_SECONDS
                )
            ),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_wallbox_data()
        except (AuthenticationError, PortalConnectionError) as err:
            _LOGGER.warning(
                "AlphaESS wallbox refresh failed during %s with status %s",
                err.step,
                getattr(err, "status", "authorization"),
            )
            raise UpdateFailed(f"AlphaESS wallbox refresh failed during {err.step}") from err
