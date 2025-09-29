# custom_components/claude_meter_reader/config_flow.py
"""Config flow for Claude Meter Reader integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

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

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_CAMERA_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="camera")
        ),
        vol.Optional(CONF_LED_ENTITY, default=DEFAULT_LED_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="light")
        ),
        vol.Optional(CONF_LED_DELAY, default=DEFAULT_LED_DELAY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=30)
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=300, max=3600)
        ),
        vol.Optional(CONF_CLAUDE_PROMPT, default=DEFAULT_CLAUDE_PROMPT): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    # Validate camera entity exists
    camera_state = hass.states.get(data[CONF_CAMERA_ENTITY])
    if camera_state is None:
        raise InvalidCamera
    
    # Validate LED entity exists (if provided)
    if data.get(CONF_LED_ENTITY):
        led_state = hass.states.get(data[CONF_LED_ENTITY])
        if led_state is None:
            raise InvalidLed
    
    # Validate API key format
    if not data[CONF_API_KEY].startswith("sk-ant-"):
        raise InvalidAuth
    
    return {"title": f"Claude Reader - {camera_state.attributes.get('friendly_name', data[CONF_CAMERA_ENTITY])}"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Claude Meter Reader."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors[CONF_API_KEY] = "invalid_auth"
            except InvalidCamera:
                errors[CONF_CAMERA_ENTITY] = "invalid_camera"
            except InvalidLed:
                errors[CONF_LED_ENTITY] = "invalid_led"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an option flow for Claude Meter Reader."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LED_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_LED_ENTITY, self.config_entry.data.get(CONF_LED_ENTITY, DEFAULT_LED_ENTITY)
                    ),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="light")),
                vol.Optional(
                    CONF_LED_DELAY,
                    default=self.config_entry.options.get(
                        CONF_LED_DELAY, self.config_entry.data.get(CONF_LED_DELAY, DEFAULT_LED_DELAY)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=3600)),
                vol.Optional(
                    CONF_CLAUDE_PROMPT,
                    default=self.config_entry.options.get(
                        CONF_CLAUDE_PROMPT, self.config_entry.data.get(CONF_CLAUDE_PROMPT, DEFAULT_CLAUDE_PROMPT)
                    ),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

class InvalidCamera(HomeAssistantError):
    """Error to indicate the camera entity is invalid."""

class InvalidLed(HomeAssistantError):
    """Error to indicate the LED entity is invalid."""