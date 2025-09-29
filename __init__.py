# custom_components/claude_meter_reader/__init__.py
"""The Claude Meter Reader integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_API_KEY, CONF_CAMERA_ENTITY, CONF_SCAN_INTERVAL, SERVICE_READ_METER
from .coordinator import ClaudeMeterReaderCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Claude Meter Reader from a config entry."""
    coordinator = ClaudeMeterReaderCoordinator(hass, entry)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register the read_meter service
    async def handle_read_meter(call):
        """Handle the read_meter service call."""
        await coordinator.async_read_meter()
    
    hass.services.async_register(DOMAIN, SERVICE_READ_METER, handle_read_meter)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove service if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_READ_METER)
    
    return unload_ok