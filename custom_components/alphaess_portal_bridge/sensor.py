"""Read-only wallbox entities for AlphaESS Wallbox Bridge."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AlphaESSWallboxCoordinator
from .const import CONF_SYSTEM_SERIAL, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up wallbox sensors."""
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AlphaESSWallboxStatusSensor(coordinator, entry),
            AlphaESSWallboxPowerSensor(coordinator, entry),
            AlphaESSWallboxModeSensor(coordinator, entry),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Serialnummer", "sn"),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Modell", "model"),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Phasenwahl", "phase"),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Startleistung", "startUpPower", UnitOfPower.WATT),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Software", "softwareVersion"),
            AlphaESSWallboxInformationSensor(coordinator, entry, "Hardware", "hardwareVersion"),
        ]
    )


def _first_value(data: dict[str, Any] | None, *keys: str) -> Any:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def _wallbox_configuration_object(value: Any, serial: str | None) -> dict[str, Any]:
    """Find the portal object representing the configured wallbox."""
    if not serial:
        return {}
    if isinstance(value, dict):
        if any(item == serial for item in value.values()):
            return value
        for item in value.values():
            found = _wallbox_configuration_object(item, serial)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _wallbox_configuration_object(item, serial)
            if found:
                return found
    return {}


class AlphaESSWallboxEntity(CoordinatorEntity[AlphaESSWallboxCoordinator], SensorEntity):
    """Base entity shared by AlphaESS wallbox sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        system_serial = entry.data[CONF_SYSTEM_SERIAL]
        self._attr_unique_id = f"{system_serial}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_serial)},
            name="AlphaESS Wallbox",
            manufacturer="AlphaESS",
            model="SMILE-EVCT11",
        )

    @property
    def _status(self) -> dict[str, Any] | None:
        return self.coordinator.data.get("wallbox_status") if self.coordinator.data else None


class AlphaESSWallboxStatusSensor(AlphaESSWallboxEntity):
    """Wallbox connection and charging status."""

    _attr_name = "Status"

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "status")

    @property
    def native_value(self) -> str | int | None:
        return _first_value(self._status, "status", "chargingStatus", "state")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        serial = self.coordinator.data.get("wallbox_serial") if self.coordinator.data else None
        if serial:
            attrs["wallbox_serial"] = serial
        source = self.coordinator.data.get("wallbox_status_source") if self.coordinator.data else None
        if source:
            attrs["data_source"] = source
        allowed_keys = {
            "status", "chargingStatus", "state", "power", "chargingPower",
            "currentPower", "realPower", "mode", "chargeMode", "chargingMode",
            "strategy", "current", "voltage", "phase", "energy", "sessionEnergy",
            "startTime", "endTime", "faultCode",
        }
        for key in allowed_keys:
            value = (self._status or {}).get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                attrs[key] = value
        return attrs


class AlphaESSWallboxPowerSensor(AlphaESSWallboxEntity):
    """Current charging power reported by the portal."""

    _attr_name = "Leistung"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "power")

    @property
    def native_value(self) -> float | None:
        value = _first_value(self._status, "power", "chargingPower", "currentPower", "realPower")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None


class AlphaESSWallboxModeSensor(AlphaESSWallboxEntity):
    """Configured wallbox charging mode from the portal."""

    _attr_name = "Lademodus"

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "mode")

    @property
    def native_value(self) -> str | int | None:
        configuration = (self.coordinator.data or {}).get("configuration") or {}
        serial = (self.coordinator.data or {}).get("wallbox_serial")
        wallbox = _wallbox_configuration_object(configuration, serial)
        settings = wallbox.get("g1T") if isinstance(wallbox.get("g1T"), dict) else {}
        modes = {0: "ECO-Ladung", 1: "Langsamladung", 2: "Schonladung", 3: "Schnellladung", 4: "Kundenspezifische Ladung"}
        return modes.get(settings.get("chargeMode"))


class AlphaESSWallboxInformationSensor(AlphaESSWallboxEntity):
    """One read-only item from the portal wallbox configuration."""

    def __init__(self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry, name: str, key: str, unit: str | None = None) -> None:
        super().__init__(coordinator, entry, f"information_{key}")
        self._attr_name = name
        self._key = key
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> str | int | float | None:
        configuration = (self.coordinator.data or {}).get("configuration") or {}
        serial = (self.coordinator.data or {}).get("wallbox_serial")
        return _wallbox_configuration_object(configuration, serial).get(self._key)
