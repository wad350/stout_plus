from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr
import voluptuous as vol
import httpx

from . import DOMAIN


async def test_connection(host: str) -> bool:
    """Test if the boiler is reachable."""
    try:
        async with httpx.AsyncClient(verify=False, trust_env=False) as client:
            response = await client.get(f"http://{host}/main_params", timeout=10)
            return response.status_code == 200
    except (httpx.RequestError, httpx.TimeoutException):
        return False


class StoutPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Stout Plus integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input["host"]
            if await test_connection(host):
                return self.async_create_entry(title="Stout Plus Boiler", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({vol.Required("host"): str})

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow for this handler."""
        return StoutPlusOptionsFlowHandler(config_entry)


class StoutPlusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Stout Plus."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the host in the existing config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={"host": user_input["host"]}
            )

            # Ensure device identifiers are updated
            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(identifiers={(DOMAIN, self.config_entry.entry_id)})
            if device:
                device_registry.async_update_device(
                    device.id, new_identifiers={(DOMAIN, self.config_entry.entry_id)}
                )

            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema({vol.Required("host", default=self.config_entry.data["host"]): str})

        return self.async_show_form(step_id="init", data_schema=data_schema)
