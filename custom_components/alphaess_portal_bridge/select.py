"""Charging mode selection for AlphaESS Wallbox Bridge."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AuthenticationError, PortalConnectionError
from .const import CONF_SYSTEM_SERIAL, DOMAIN
from .coordinator import AlphaESSWallboxCoordinator

MODE_VALUES = {
    "ECO-Ladung": 0,
    "Langsamladung": 1,
    "Schonladung": 2,
    "Schnellladung": 3,
    "Kundenspezifische Ladung": 4,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlphaESSWallboxModeSelect(coordinator, entry)])


class AlphaESSWallboxModeSelect(CoordinatorEntity[AlphaESSWallboxCoordinator], SelectEntity):
    """Set the portal charge strategy while preserving all other settings."""

    _attr_has_entity_name = True
    _attr_name = "Lademodus"
    _attr_options = list(MODE_VALUES)

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        system_serial = entry.data[CONF_SYSTEM_SERIAL]
        self._attr_unique_id = f"{system_serial}_charge_mode_select"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_serial)}, name="AlphaESS Wallbox",
            manufacturer="AlphaESS", model="SMILE-EVCT11",
        )

    @property
    def current_option(self) -> str | None:
        configuration = (self.coordinator.data or {}).get("configuration") or {}
        serial = (self.coordinator.data or {}).get("wallbox_serial")
        wallbox = self.coordinator.api._find_wallbox_data(configuration, serial)
        settings = wallbox.get("g1T") if isinstance(wallbox.get("g1T"), dict) else {}
        return next((name for name, value in MODE_VALUES.items() if value == settings.get("chargeMode")), None)

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.api.async_update_wallbox_settings(charge_mode=MODE_VALUES[option])
        except (AuthenticationError, PortalConnectionError, ValueError) as err:
            raise HomeAssistantError("Der Lademodus wurde vom Portal nicht übernommen") from err
        await self.coordinator.async_request_refresh()
