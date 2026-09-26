"""Custom charging current setting for AlphaESS Wallbox Bridge."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AuthenticationError, PortalConnectionError
from .const import CONF_SYSTEM_SERIAL, DOMAIN
from .coordinator import AlphaESSWallboxCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlphaESSWallboxChargeCurrentNumber(coordinator, entry)])


class AlphaESSWallboxChargeCurrentNumber(CoordinatorEntity[AlphaESSWallboxCoordinator], NumberEntity):
    """Set the permitted current for the custom charge strategy."""

    _attr_has_entity_name = True
    _attr_name = "Kundenspezifischer Ladestrom"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 6
    _attr_native_max_value = 16
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        system_serial = entry.data[CONF_SYSTEM_SERIAL]
        self._attr_unique_id = f"{system_serial}_custom_charge_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_serial)}, name="AlphaESS Wallbox",
            manufacturer="AlphaESS", model="SMILE-EVCT11",
        )

    def _settings(self) -> dict:
        configuration = (self.coordinator.data or {}).get("configuration") or {}
        serial = (self.coordinator.data or {}).get("wallbox_serial")
        wallbox = self.coordinator.api._find_wallbox_data(configuration, serial)
        return wallbox.get("g1T") if isinstance(wallbox.get("g1T"), dict) else {}

    @property
    def native_value(self) -> float | None:
        value = self._settings().get("chargeCurrent")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def available(self) -> bool:
        return super().available and self._settings().get("chargeMode") == 4

    async def async_set_native_value(self, value: float) -> None:
        if self._settings().get("chargeMode") != 4:
            raise HomeAssistantError("Wähle zuerst Kundenspezifische Ladung")
        try:
            await self.coordinator.api.async_update_wallbox_settings(charge_current=int(value))
        except (AuthenticationError, PortalConnectionError, ValueError) as err:
            raise HomeAssistantError("Der Ladestrom wurde vom Portal nicht übernommen") from err
        await self.coordinator.async_request_refresh()
