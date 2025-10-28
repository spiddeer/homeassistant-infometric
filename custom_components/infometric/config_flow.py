"""Config flow for Infometric integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_URL, CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, DEFAULT_NAME, DEFAULT_URL

from .infometric import InfometricClient


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Infometric."""

    VERSION = 1
    _options = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Normalize URL (strip trailing slash)
            url = user_input[CONF_URL].rstrip("/")
            if not url.startswith("http"):
                errors["base"] = "invalid_url"
            else:
                # Uniqueness check: same URL + username
                for entry in self._async_current_entries():
                    if (
                        entry.data.get(CONF_URL, "").rstrip("/") == url
                        and entry.data.get(CONF_USERNAME) == user_input[CONF_USERNAME]
                    ):
                        return self.async_abort(reason="already_configured")

                client = InfometricClient(
                    url,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                try:
                    await client.authenticate(
                        aiohttp_client.async_get_clientsession(self.hass)
                    )
                except Exception as auth_err:  # Differentiate later if needed
                    errors["base"] = "auth_failed"
                else:
                    user_input[CONF_URL] = url
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, DEFAULT_NAME), data=user_input
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=f"{DEFAULT_URL}/"): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle YAML import (deprecated)."""
        return await self.async_step_user(import_data)
