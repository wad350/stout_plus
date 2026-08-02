"""Config flow for Stout Plus."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import StoutPlusApi, StoutPlusApiError
from .const import DOMAIN, REQUEST_TIMEOUT


class StoutPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stout Plus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setup initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            if await self._async_test_connection(host):
                return self.async_create_entry(
                    title=f"Stout Plus ({host})", data={CONF_HOST: host}
                )
            errors["base"] = "cannot_connect"

        schema = vol.Schema({vol.Required(CONF_HOST): vol.All(str, _normalize_host)})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _async_test_connection(self, host: str) -> bool:
        api = StoutPlusApi(async_get_clientsession(self.hass), host, REQUEST_TIMEOUT)
        try:
            await api.async_get("main_params")
        except StoutPlusApiError:
            return False
        return True

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> StoutPlusOptionsFlowHandler:
        """Return the options flow."""
        return StoutPlusOptionsFlowHandler(config_entry)


class StoutPlusOptionsFlowHandler(config_entries.OptionsFlow):
    """Allow the boiler address to be changed."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            api = StoutPlusApi(
                async_get_clientsession(self.hass), host, REQUEST_TIMEOUT
            )
            try:
                await api.async_get("main_params")
            except StoutPlusApiError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, CONF_HOST: host},
                    unique_id=host.lower(),
                )
                return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST, default=self._config_entry.data[CONF_HOST]
                ): vol.All(str, _normalize_host)
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


def _normalize_host(host: str) -> str:
    """Normalize the host accepted from the UI."""
    normalized = host.strip().removeprefix("http://").rstrip("/")
    if not normalized or "/" in normalized or normalized.startswith("https:"):
        raise vol.Invalid("Enter an IP address or host name without a path")
    return normalized
