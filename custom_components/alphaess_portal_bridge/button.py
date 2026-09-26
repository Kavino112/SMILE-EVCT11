"""Guarded wallbox controls for AlphaESS Wallbox Bridge."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AuthenticationError, PortalConnectionError
from .const import CONF_SYSTEM_SERIAL, DOMAIN
from .coordinator import AlphaESSWallboxCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up guarded start and stop buttons."""
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AlphaESSWallboxControlButton(coordinator, entry, "START"),
            AlphaESSWallboxControlButton(coordinator, entry, "STOP"),
        ]
    )


class AlphaESSWallboxControlButton(
    CoordinatorEntity[AlphaESSWallboxCoordinator], ButtonEntity
):
    """Expose a wallbox control only when the live state permits it."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry, control: str
    ) -> None:
        super().__init__(coordinator)
        self._control = control
        system_serial = entry.data[CONF_SYSTEM_SERIAL]
        self._attr_unique_id = f"{system_serial}_{control.lower()}"
        self._attr_name = "Laden starten" if control == "START" else "Laden stoppen"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_serial)},
            name="AlphaESS Wallbox",
            manufacturer="AlphaESS",
            model="SMILE-EVCT11",
        )

    @property
    def available(self) -> bool:
        if not super().available or not self.coordinator.data:
            return False
        status_data = self.coordinator.data.get("wallbox_status") or {}
        status = status_data.get("status") if isinstance(status_data, dict) else None
        allowed = (
            {"PendingStart", "ChargingStopped", "CharingStopped"}
            if self._control == "START"
            else {"Charging"}
        )
        return status in allowed

    async def async_press(self) -> None:
        """Recheck the portal state immediately before writing a command."""
        try:
            await self.coordinator.api.async_control_wallbox(self._control)
        except (AuthenticationError, PortalConnectionError) as err:
            raise HomeAssistantError("Wallbox command was rejected by the live status check") from err
        await self.coordinator.async_request_refresh()
