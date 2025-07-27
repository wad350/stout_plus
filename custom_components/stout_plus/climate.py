from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import httpx

from . import DOMAIN

POLLING_INTERVAL = timedelta(seconds=2)  # Интервал опроса в 2 секунды


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the climate entities."""
    host = entry.data["host"]
    entry_id = entry.entry_id
    climates = [
        BoilerClimateEntity(host, entry_id),
        RoomClimateEntity(host, entry_id),
    ]
    async_add_entities(climates)

    async def update_climates(*_):
        for climate in climates:
            await climate.async_update()

    async_track_time_interval(hass, update_climates, POLLING_INTERVAL)


class BoilerClimateEntity(ClimateEntity):
    """Representation of the boiler climate entity."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.TURN_ON |
        ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, host: str, entry_id: str):
        """Initialize the boiler climate entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_boiler_climate"
        self._attr_name = "Boiler Climate"
        self._attr_target_temperature = 30.0
        self._attr_min_temp = 15.0
        self._attr_max_temp = 40.0
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_current_temperature = 30.0

    async def async_update(self):
        """Fetch the latest state."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/main_params")
                response.raise_for_status()
                data = response.json()

                self._attr_current_temperature = float(data["ActValTempCarrier"])
                self._attr_target_temperature = float(data["SetTempCarrier"])
                set_mode = int(data["setMode"])
                self._attr_hvac_mode = HVACMode.HEAT if set_mode == 0 else HVACMode.OFF
        except (httpx.RequestError, ValueError, KeyError):
            pass  # Keep previous state on error

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            try:
                async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                    await client.post(
                        f"http://{self._host}/change_crrtrg",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content=f"[{temperature}]"
                    )
                self._attr_target_temperature = temperature
                self.async_write_ha_state()
            except httpx.RequestError:
                pass

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                if hvac_mode == HVACMode.HEAT:
                    await client.post(
                        f"http://{self._host}/switch_mode",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content="[0]"
                    )
                elif hvac_mode == HVACMode.OFF:
                    await client.post(
                        f"http://{self._host}/switch_mode",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content="[4]"
                    )
                self._attr_hvac_mode = hvac_mode
        except httpx.RequestError:
            pass
        self.async_write_ha_state()
        await self.async_update()

    @property
    def target_temperature_step(self):
        """Return the temperature step."""
        return 0.1

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._attr_current_temperature


class RoomClimateEntity(ClimateEntity):
    """Representation of the room climate entity."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.TURN_ON |
        ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, host: str, entry_id: str):
        """Initialize the room climate entity."""
        self._host = host
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_room_climate"
        self._attr_name = "Room Climate"
        self._attr_target_temperature = 22.0
        self._attr_min_temp = 18.0
        self._attr_max_temp = 28.0
        self._attr_current_temperature = 20.0
        self._attr_hvac_mode = HVACMode.OFF  # Установим начальный режим

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._attr_hvac_mode

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                if hvac_mode == HVACMode.HEAT:
                    # Включение режима с data-raw '2'
                    await client.post(
                        f"http://{self._host}/switch_mode",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content="[2]"
                    )
                elif hvac_mode == HVACMode.OFF:
                    # Выключение режима с data-raw '4'
                    await client.post(
                        f"http://{self._host}/switch_mode",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content="[4]"
                    )
                self._attr_hvac_mode = hvac_mode
        except httpx.RequestError:
            pass
        self.async_write_ha_state()
        await self.async_update()

    async def async_update(self):
        """Fetch the latest state."""
        try:
            async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                response = await client.get(f"http://{self._host}/main_params")
                response.raise_for_status()
                data = response.json()

                self._attr_current_temperature = float(data["TempInRoom"])
                self._attr_target_temperature = float(data["setTempRoomMode"])
                room_mode = int(data["setMode"])
                self._attr_hvac_mode = HVACMode.HEAT if room_mode == 2 else HVACMode.OFF
        except (httpx.RequestError, ValueError, KeyError):
            pass  # Keep previous state on error
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set the target room temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            try:
                async with httpx.AsyncClient(verify=False, trust_env=False) as client:
                    await client.post(
                        f"http://{self._host}/change_rmtrg",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                        content=f"[{temperature}]"
                    )
                self._attr_target_temperature = temperature
            except httpx.RequestError:
                pass
        self.async_write_ha_state()

    @property
    def target_temperature_step(self):
        """Return the temperature step."""
        return 0.1

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Boiler Controller",
            "manufacturer": "Stout",
            "model": "Stout Plus 9kvt",
        }

