"""Binary wallbox states for AlphaESS Wallbox Bridge."""
# ---------------------------------------------------------------------------
# Community-Build fuer https://www.storion4you.de/
# G2T-Erweiterung fuer SMILE-G3-EVCT11/S: Kavino
# Basierend auf dem Ausgangsprojekt wfa001/SMILE-EVCT11.
# Details und Attribution: siehe NOTICE.md im Paket.
# ---------------------------------------------------------------------------
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AlphaESSWallboxCoordinator
from .entity import AlphaESSWallboxEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """No binary sensors are currently exposed."""
    async_add_entities([])


class AlphaESSVehicleConnectedBinarySensor(AlphaESSWallboxEntity, BinarySensorEntity):
    """Whether a charging cable/vehicle is inserted according to live status."""

    _attr_name = "Fahrzeug angeschlossen"

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "vehicle_connected")

    @property
    def is_on(self) -> bool | None:
        status_data = (self.coordinator.data or {}).get("wallbox_status") or {}
        status = status_data.get("status") if isinstance(status_data, dict) else None
        if not isinstance(status, str):
            return None
        return status != "NotInsertedGun"


class AlphaESSGunLockBinarySensor(AlphaESSWallboxEntity, BinarySensorEntity):
    """Whether the charging gun/cable is locked."""

    _attr_name = "Ladestecker verriegelt"

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "gun_locked")

    @property
    def is_on(self) -> bool | None:
        status_data = (self.coordinator.data or {}).get("wallbox_status") or {}
        value = status_data.get("gunIsLock") if isinstance(status_data, dict) else None
        return value if isinstance(value, bool) else None


class AlphaESSGunLineSelfLockEnabledBinarySensor(AlphaESSWallboxEntity, BinarySensorEntity):
    """Configured cable self-lock setting exposed by G2T."""

    _attr_name = "Kabel-Selbstverriegelung aktiviert"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "gun_line_self_lock_enabled")

    @property
    def available(self) -> bool:
        return super().available and self.settings_generation == "g2T" and self.settings.get("isSupportGunLineSelfLock") is True

    @property
    def is_on(self) -> bool | None:
        value = self.settings.get("gunLineSelfLockEnable")
        return value if isinstance(value, bool) else None


class AlphaESSInstallerControlBinarySensor(AlphaESSWallboxEntity, BinarySensorEntity):
    """Whether the portal reports installer control as allowed."""

    _attr_name = "Installateursteuerung erlaubt"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "installer_control_allowed")

    @property
    def is_on(self) -> bool | None:
        value = self.wallbox.get("allowInstallersControl")
        return value if isinstance(value, bool) else None
