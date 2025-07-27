from homeassistant.components.select import SelectEntity
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import httpx

from . import DOMAIN

POLLING_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the select entities."""
    host = entry.data["host"]
    entry_id = entry.entry_id
    selects = [
        BoilerPowerDaySelect(host, entry_id),
        BoilerPowerNightSelect(host, entry_id),
    ]
    async_add_entities(selects)

    async def update_selects(*_):
        for select in selects:
            await select.async_update()

    async_track_time_interval(hass, update_selects, POLLING_INTERVAL)


class BoilerPowerDaySelect(SelectEntity):
    """Representation of the day power level select entity."""

    _attr_options = ["1.5", "3.0", "4.5", "6.0", "7.5", "9.0"]
    _attr_name = "Boiler Day Power Limit"
    _attr_icon = "mdi:flash"

    def __init__(self, host: str, entry_id: str):
        """Initialize the select entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_power_day"
        self._attr_current_option = None

    @property
    def device_info(self):
        """Return device information for linking the select entity to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_select_option(self, option: str):
        """Handle the selection of an option."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                await client.post(
                    f"http://{self._host}/apply_power_day",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"amountActiveLevelsPerDay": option},
                )
                self._attr_current_option = option
                self.async_write_ha_state()
        except (httpx.RequestError, ValueError):
            pass  # Keep the previous state on error

    async def async_update(self):
        """Fetch the current power limit."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                # Convert step value to power level
                step = int(data.get("amountActiveLevelsPerDay", 1))
                power_level = step * 1.5
                self._attr_current_option = f"{power_level:.1f}" if power_level in [float(opt) for opt in self._attr_options] else None
        except (httpx.RequestError, ValueError, KeyError):
            self._attr_current_option = None

        self.async_write_ha_state()


class BoilerPowerNightSelect(SelectEntity):
    """Representation of the night power level select entity."""

    _attr_options = ["1.5", "3.0", "4.5", "6.0", "7.5", "9.0"]
    _attr_name = "Boiler Night Power Limit"
    _attr_icon = "mdi:weather-night"

    def __init__(self, host: str, entry_id: str):
        """Initialize the select entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_power_night"
        self._attr_current_option = None

    @property
    def device_info(self):
        """Return device information for linking the select entity to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_select_option(self, option: str):
        """Handle the selection of an option."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                await client.post(
                    f"http://{self._host}/apply_power_day",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"amountActiveLevelsAtNight": option},
                )
                self._attr_current_option = option
                self.async_write_ha_state()
        except (httpx.RequestError, ValueError):
            pass  # Keep the previous state on error

    async def async_update(self):
        """Fetch the current power limit."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                # Convert step value to power level
                step = int(data.get("amountActiveLevelsAtNight", 1))
                power_level = step * 1.5
                self._attr_current_option = f"{power_level:.1f}" if power_level in [float(opt) for opt in self._attr_options] else None
        except (httpx.RequestError, ValueError, KeyError):
            self._attr_current_option = None

        self.async_write_ha_state()
