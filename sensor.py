# custom_components/claude_meter_reader/sensor.py
"""Sensor platform for Claude Meter Reader."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ClaudeMeterReaderCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        ClaudeMeterReaderSensor(coordinator),
        ClaudeMeterReaderStatusSensor(coordinator),
        ClaudeMeterReaderLastReadingSensor(coordinator),
    ])

class ClaudeMeterReaderSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(self, coordinator: ClaudeMeterReaderCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Claude Wasserzähler"
        self._attr_unique_id = f"{DOMAIN}_water_meter"
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._restored_value = None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore last state
        if (restored_state := await self.async_get_last_state()) is not None:
            try:
                self._restored_value = float(restored_state.state)
                self.coordinator.logger.info(
                    "Restored last meter value: %s", self._restored_value
                )
            except (ValueError, TypeError):
                self.coordinator.logger.warning(
                    "Could not restore last state: %s", restored_state.state
                )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        # If coordinator has no data yet, use restored value
        if self.coordinator.data is None:
            return self._restored_value
        
        current_value = self.coordinator.data.get("value")
        
        # If current read failed but we have a restored value, keep using it
        if current_value is None and self._restored_value is not None:
            return self._restored_value
            
        return current_value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
        
        attrs = {
            "status": self.coordinator.data.get("status"),
            "last_reading": self.coordinator.data.get("last_reading"),
            "camera_entity": self.coordinator.camera_entity,
            "led_entity": self.coordinator.led_entity,
            "led_delay": self.coordinator.led_delay,
        }
        
        if "error" in self.coordinator.data:
            attrs["error"] = self.coordinator.data["error"]
        
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

class ClaudeMeterReaderStatusSensor(CoordinatorEntity, SensorEntity):
    """Status sensor for Claude Meter Reader."""

    def __init__(self, coordinator: ClaudeMeterReaderCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Claude Wasserzähler Status"
        self._attr_unique_id = f"{DOMAIN}_status"
        self._attr_icon = "mdi:information"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.coordinator.data is None:
            return "unknown"
        return self.coordinator.data.get("status", "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
        
        attrs = {
            "last_reading": self.coordinator.data.get("last_reading"),
            "update_interval": self.coordinator.update_interval.total_seconds(),
        }
        
        if "error" in self.coordinator.data:
            attrs["last_error"] = self.coordinator.data["error"]
        
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True  # Status sensor is always available

class ClaudeMeterReaderLastReadingSensor(CoordinatorEntity, SensorEntity):
    """Last reading timestamp sensor for Claude Meter Reader."""

    def __init__(self, coordinator: ClaudeMeterReaderCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Claude Wasserzähler Letzte Ablesung"
        self._attr_unique_id = f"{DOMAIN}_last_reading"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.coordinator.data is None:
            return None
        last_reading = self.coordinator.data.get("last_reading")
        if last_reading:
            # Convert ISO string to German date format
            try:
                dt = dt_util.parse_datetime(last_reading)
                if dt:
                    # Format: "28.09.2025 17:45"
                    return dt.strftime("%d.%m.%Y %H:%M")
            except (ValueError, TypeError):
                pass
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
        
        attrs = {
            "status": self.coordinator.data.get("status"),
            "update_interval": self.coordinator.update_interval.total_seconds(),
        }
        
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None