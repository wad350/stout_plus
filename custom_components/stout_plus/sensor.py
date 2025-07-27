from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfPressure, UnitOfTemperature
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import httpx
import re

from . import DOMAIN

POLLING_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities."""
    host = entry.data["host"]
    entry_id = entry.entry_id
    sensors = [
        BoilerPowerSensor(host, entry_id),
        BoilerPressureSensor(host, entry_id),
        BoilerRoomTemperatureSensor(host, entry_id),
    ]
    async_add_entities(sensors)

    async def update_sensors(*_):
        for sensor in sensors:
            await sensor.async_update()

    async_track_time_interval(hass, update_sensors, POLLING_INTERVAL)


class BoilerPowerSensor(SensorEntity):
    """Representation of the current power consumption sensor."""

    _attr_name = "Boiler Power Consumption"
    _attr_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_device_class = "power"
    _attr_state_class = "measurement"

    def __init__(self, host: str, entry_id: str):
        """Initialize the power sensor."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_power"
        self._attr_state = None

    @property
    def state(self):
        """Return the current state of the power sensor."""
        return self._attr_state

    @property
    def device_info(self):
        """Return device information for linking sensors to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_update(self):
        """Fetch the latest power consumption."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                self._attr_state = float(data.get("CurrPwr_str", 0))
        except (httpx.RequestError, ValueError):
            self._attr_state = None

        self.async_write_ha_state()


class BoilerPressureSensor(SensorEntity):
    """Representation of the current pressure sensor."""

    _attr_name = "Boiler Pressure"
    _attr_unit_of_measurement = UnitOfPressure.BAR
    _attr_device_class = "pressure"
    _attr_state_class = "measurement"

    def __init__(self, host: str, entry_id: str):
        """Initialize the pressure sensor."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_pressure"
        self._attr_state = None

    @property
    def state(self):
        """Return the current state of the pressure sensor."""
        return self._attr_state

    @property
    def device_info(self):
        """Return device information for linking sensors to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_update(self):
        """Fetch the latest pressure value."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/other_params")
                response.raise_for_status()
                data = response.json()

                act_press = data.get("ActPress", "")
                match = re.search(r"[\d.]+", act_press)
                self._attr_state = float(match.group(0)) if match else None
        except (httpx.RequestError, ValueError, AttributeError):
            self._attr_state = None

        self.async_write_ha_state()


class BoilerRoomTemperatureSensor(SensorEntity):
    """Representation of the room temperature sensor (SensTemp0)."""

    _attr_name = "Room Temperature"
    _attr_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = "temperature"
    _attr_state_class = "measurement"

    def __init__(self, host: str, entry_id: str):
        """Initialize the room temperature sensor."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_room_temp"
        self._attr_state = None

    @property
    def state(self):
        """Return the current state of the room temperature sensor."""
        return self._attr_state

    @property
    def native_unit_of_measurement(self):
        """Return the native unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def device_info(self):
        """Return device information for linking sensors to the boiler device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    async def async_update(self):
        """Fetch the latest room temperature value."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/additional_params")
                response.raise_for_status()
                data = response.json()

                sens_temp0 = data.get("SensTemp0", "")
                match = re.search(r"[\d.-]+", sens_temp0)
                self._attr_state = round(float(match.group(0)), 1) if match else None
        except (httpx.RequestError, ValueError, AttributeError):
            self._attr_state = None

        self.async_write_ha_state()

