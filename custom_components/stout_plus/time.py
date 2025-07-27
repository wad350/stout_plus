from homeassistant.components.time import TimeEntity
from homeassistant.helpers.event import async_track_time_interval
from datetime import datetime, time, timedelta
import httpx

from . import DOMAIN

POLLING_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the time entities."""
    host = entry.data["host"]
    entry_id = entry.entry_id
    time_entities = [
        BoilerNightTimeEntity(host, entry_id),
        BoilerDayTimeEntity(host, entry_id),
    ]
    async_add_entities(time_entities)

    async def update_time_entities(*_):
        for entity in time_entities:
            await entity.async_update()

    async_track_time_interval(hass, update_time_entities, POLLING_INTERVAL)


class BoilerNightTimeEntity(TimeEntity):
    """Representation of the night time start entity."""

    _attr_name = "Boiler Night Start Time"
    _attr_icon = "mdi:timer-settings-outline"
    _attr_has_entity_name = True

    def __init__(self, host: str, entry_id: str):
        """Initialize the time entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_night_time"
        self._attr_native_value = None

    @property
    def device_info(self):
        """Return device information for linking the entity to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_set_value(self, value: time):
        """Handle setting the time value."""
        try:
            formatted_value = value.strftime("%H:%M")
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                await client.post(
                    f"http://{self._host}/apply_power_day",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"nightTime": formatted_value},
                )
                self._attr_native_value = value
                self.async_write_ha_state()
        except (httpx.RequestError, ValueError):
            pass

    async def async_update(self):
        """Fetch the current time value."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                time_str = data.get("nightTime", "22:00")
                self._attr_native_value = datetime.strptime(time_str, "%H:%M").time()
        except (httpx.RequestError, ValueError, KeyError):
            self._attr_native_value = None

        self.async_write_ha_state()


class BoilerDayTimeEntity(TimeEntity):
    """Representation of the day time start entity."""

    _attr_name = "Boiler Day Start Time"
    _attr_icon = "mdi:timer-settings"
    _attr_has_entity_name = True

    def __init__(self, host: str, entry_id: str):
        """Initialize the time entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_day_time"
        self._attr_native_value = None

    @property
    def device_info(self):
        """Return device information for linking the entity to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_set_value(self, value: time):
        """Handle setting the time value."""
        try:
            formatted_value = value.strftime("%H:%M")
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                await client.post(
                    f"http://{self._host}/apply_power_day",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"dayTime": formatted_value},
                )
                self._attr_native_value = value
                self.async_write_ha_state()
        except (httpx.RequestError, ValueError):
            pass

    async def async_update(self):
        """Fetch the current time value."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                time_str = data.get("dayTime", "07:00")
                self._attr_native_value = datetime.strptime(time_str, "%H:%M").time()
        except (httpx.RequestError, ValueError, KeyError):
            self._attr_native_value = None

        self.async_write_ha_state()
