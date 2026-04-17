"""Config flow for the transitapp integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import TransitAppAuthError, TransitAppClient, TransitAppConnectionError
from .const import (
    CONF_RADIUS,
    DEFAULT_RADIUS_METERS,
    DOMAIN,
    MAX_RADIUS_METERS,
    MIN_RADIUS_METERS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS_METERS): NumberSelector(
            NumberSelectorConfig(
                min=MIN_RADIUS_METERS,
                max=MAX_RADIUS_METERS,
                step=50,
                unit_of_measurement="m",
                mode=NumberSelectorMode.SLIDER,
            )
        ),
    }
)


class TransitAppConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for transitapp."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_API_KEY: user_input[CONF_API_KEY]})
            client = TransitAppClient(
                async_get_clientsession(self.hass), user_input[CONF_API_KEY]
            )
            try:
                await client.async_probe()
            except TransitAppAuthError:
                errors["base"] = "invalid_auth"
            except TransitAppConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="Transit",
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_RADIUS: int(user_input[CONF_RADIUS]),
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
