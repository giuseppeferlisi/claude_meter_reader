# custom_components/claude_meter_reader/coordinator.py
"""DataUpdateCoordinator for Claude Meter Reader."""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.components.camera import async_get_image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_CAMERA_ENTITY,
    CONF_CLAUDE_PROMPT,
    CONF_LED_ENTITY,
    CONF_LED_DELAY,
    CONF_SCAN_INTERVAL,
    DEFAULT_CLAUDE_PROMPT,
    DEFAULT_LED_ENTITY,
    DEFAULT_LED_DELAY,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class ClaudeMeterReaderCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        self.entry = entry
        self.api_key = entry.data[CONF_API_KEY]
        self.camera_entity = entry.data[CONF_CAMERA_ENTITY]
        self.claude_prompt = entry.options.get(CONF_CLAUDE_PROMPT) or entry.data.get(CONF_CLAUDE_PROMPT, DEFAULT_CLAUDE_PROMPT)
        self.led_entity = entry.options.get(CONF_LED_ENTITY) or entry.data.get(CONF_LED_ENTITY, DEFAULT_LED_ENTITY)
        self.led_delay = entry.options.get(CONF_LED_DELAY) or entry.data.get(CONF_LED_DELAY, DEFAULT_LED_DELAY)
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL) or entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        return await self._read_meter_internal()

    async def async_read_meter(self) -> dict[str, Any]:
        """Read meter on demand and update data."""
        data = await self._read_meter_internal()
        # Update the coordinator's data
        self.async_set_updated_data(data)
        return data

    async def _read_meter_internal(self) -> dict[str, Any]:
        """Internal method to read meter."""
        try:
            # Turn on LED if configured
            if self.led_entity and self.led_entity != "":
                await self._turn_on_led()
            
            # Get camera image
            image_data = await self._get_camera_image()
            if image_data is None:
                raise UpdateFailed("Failed to get camera image")

            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Call Claude API
            meter_value = await self._call_claude_api(image_b64)
            
            if meter_value is None:
                raise UpdateFailed("Failed to read meter value from Claude")
            
            return {
                "value": meter_value,
                "status": "success",
                "last_reading": dt_util.now().isoformat(),
            }
            
        except Exception as err:
            _LOGGER.error("Error reading meter: %s", err)
            return {
                "value": None,
                "status": "error",
                "error": str(err),
                "last_reading": dt_util.now().isoformat(),
            }
        finally:
            # Turn off LED after delay if configured
            if self.led_entity and self.led_entity != "":
                await self._turn_off_led_after_delay()

    async def _turn_on_led(self) -> None:
        """Turn on the LED."""
        try:
            await self.hass.services.async_call(
                "light", "turn_on", {"entity_id": self.led_entity}
            )
            _LOGGER.debug("Turned on LED: %s", self.led_entity)
        except Exception as err:
            _LOGGER.warning("Failed to turn on LED %s: %s", self.led_entity, err)

    async def _turn_off_led_after_delay(self) -> None:
        """Turn off the LED after a delay."""
        try:
            await asyncio.sleep(self.led_delay)
            await self.hass.services.async_call(
                "light", "turn_off", {"entity_id": self.led_entity}
            )
            _LOGGER.debug("Turned off LED: %s after %s seconds", self.led_entity, self.led_delay)
        except Exception as err:
            _LOGGER.warning("Failed to turn off LED %s: %s", self.led_entity, err)

    async def _get_camera_image(self) -> bytes | None:
        """Get image from camera entity."""
        try:
            camera_state = self.hass.states.get(self.camera_entity)
            if camera_state is None:
                _LOGGER.error("Camera entity %s not found", self.camera_entity)
                return None
            
            image = await async_get_image(self.hass, self.camera_entity)
            return image.content
        except HomeAssistantError as err:
            _LOGGER.error("Error getting camera image: %s", err)
            return None

    async def _call_claude_api(self, image_b64: str) -> float | None:
        """Call Claude API to read meter value with model fallback."""
        models_to_try = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620", 
            "claude-3-haiku-20240307",
        ]
        
        session = async_get_clientsession(self.hass)
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        
        for i, model in enumerate(models_to_try):
            try:
                _LOGGER.debug("Trying model: %s (attempt %d/%d)", model, i+1, len(models_to_try))
                
                payload = {
                    "model": model,
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": self.claude_prompt
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_b64
                                    }
                                }
                            ]
                        }
                    ]
                }

                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("content", [{}])[0].get("text", "").strip()
                        
                        if content == "FEHLER":
                            _LOGGER.warning("Claude couldn't read meter with model %s", model)
                            continue
                        
                        # Versuche Zahl zu extrahieren
                        try:
                            value = float(content.replace(',', '.'))
                            _LOGGER.info("Successfully read meter value: %s with model %s", value, model)
                            return value
                        except ValueError:
                            _LOGGER.warning("Invalid number format from Claude (%s): '%s'", model, content)
                            continue
                    
                    else:
                        error_text = await response.text()
                        _LOGGER.warning("Claude API error with model %s (HTTP %d): %s", 
                                      model, response.status, error_text)
                        
                        # Bei Rate Limit oder Server Error nächstes Modell versuchen
                        if response.status in [429, 500, 502, 503, 504]:
                            continue
                        # Bei anderen Fehlern (z.B. 401, 403) alle Modelle abbrechen
                        elif response.status in [401, 403]:
                            _LOGGER.error("Authentication error - check API key")
                            break

            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout with model %s", model)
                continue
            except Exception as err:
                _LOGGER.warning("Error with model %s: %s", model, err)
                continue

        _LOGGER.error("All models failed to read meter value")
        return None