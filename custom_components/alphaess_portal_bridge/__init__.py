"""Set up AlphaESS Portal Bridge."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .api import AlphaESSPortalApi
from .coordinator import AlphaESSWallboxCoordinator
from .const import CONF_SYSTEM_SERIAL, DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SELECT, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a validated portal session without exposing credentials."""
    api = AlphaESSPortalApi(hass, dict(entry.data))
    coordinator = AlphaESSWallboxCoordinator(hass, api)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    system_serial = entry.data[CONF_SYSTEM_SERIAL]
    desired_title = f"AlphaESS Wallbox {system_serial}"
    if entry.title != desired_title:
        hass.config_entries.async_update_entry(entry, title=desired_title)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the portal session."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
