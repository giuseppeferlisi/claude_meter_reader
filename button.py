# custom_components/claude_meter_reader/button.py
"""Button platform for Claude Meter Reader."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClaudeMeterReaderCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        ClaudeMeterReaderButton(coordinator),
    ])

class ClaudeMeterReaderButton(CoordinatorEntity, ButtonEntity):
    """Representation of a button."""

    def __init__(self, coordinator: ClaudeMeterReaderCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Zähler jetzt ablesen"
        self._attr_unique_id = f"{DOMAIN}_read_button"
        self._attr_icon = "mdi:eye-check"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_read_meter()