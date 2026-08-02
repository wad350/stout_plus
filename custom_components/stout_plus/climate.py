"""Climate entities for Stout Plus."""

from __future__ import annotations

from typing import Any, ClassVar

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import StoutPlusApiError
from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up climate entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        (
            BoilerClimateEntity(coordinator, entry.entry_id),
            RoomClimateEntity(coordinator, entry.entry_id),
        )
    )


class StoutPlusClimateEntity(StoutPlusEntity, ClimateEntity):
    """Shared implementation for boiler climate entities."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes: ClassVar[list[HVACMode]] = [HVACMode.HEAT, HVACMode.OFF]
    _attr_target_temperature_step = 0.1
    _endpoint = "main"

    async def _async_post(self, endpoint: str, value: str) -> None:
        try:
            await self.coordinator.api.async_post_text(endpoint, value)
        except StoutPlusApiError as err:
            raise HomeAssistantError(
                "Could not send the command to the Stout Plus boiler"
            ) from err
        await self.coordinator.async_request_refresh()


class BoilerClimateEntity(StoutPlusClimateEntity):
    """Control heating by the boiler water temperature."""

    _attr_translation_key = "boiler_temperature"
    _attr_min_temp = 15.0
    _attr_max_temp = 40.0

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_boiler_climate"

    @property
    def current_temperature(self) -> float | None:
        return _as_float(self.coordinator.data["main"].get("ActValTempCarrier"))

    @property
    def target_temperature(self) -> float | None:
        return _as_float(self.coordinator.data["main"].get("SetTempCarrier"))

    @property
    def hvac_mode(self) -> HVACMode:
        return (
            HVACMode.HEAT
            if _as_int(self.coordinator.data["main"].get("setMode")) == 0
            else HVACMode.OFF
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._async_post("change_crrtrg", f"[{temperature}]")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        value = "[0]" if hvac_mode == HVACMode.HEAT else "[4]"
        await self._async_post("switch_mode", value)


class RoomClimateEntity(StoutPlusClimateEntity):
    """Control heating by the room temperature."""

    _attr_translation_key = "room_temperature"
    _attr_min_temp = 18.0
    _attr_max_temp = 28.0

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_room_climate"

    @property
    def current_temperature(self) -> float | None:
        return _as_float(self.coordinator.data["main"].get("TempInRoom"))

    @property
    def target_temperature(self) -> float | None:
        return _as_float(self.coordinator.data["main"].get("setTempRoomMode"))

    @property
    def hvac_mode(self) -> HVACMode:
        return (
            HVACMode.HEAT
            if _as_int(self.coordinator.data["main"].get("setMode")) == 2
            else HVACMode.OFF
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._async_post("change_rmtrg", f"[{temperature}]")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        value = "[2]" if hvac_mode == HVACMode.HEAT else "[4]"
        await self._async_post("switch_mode", value)


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
