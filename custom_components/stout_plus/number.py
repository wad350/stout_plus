"""Number entities for Stout Plus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import StoutPlusApiError
from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity


@dataclass(frozen=True, kw_only=True)
class StoutPlusNumberDescription(NumberEntityDescription):
    """Describe a writable numeric setting."""

    endpoint: str
    source_key: str
    command: str


NUMBERS: tuple[StoutPlusNumberDescription, ...] = (
    StoutPlusNumberDescription(
        key="dhw_target_temperature",
        name="Domestic hot water target temperature",
        endpoint="main",
        source_key="settedTemperatureOfDHW",
        command="change_dhwtrg",
        native_min_value=40.0,
        native_max_value=75.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:water-thermometer",
    ),
    StoutPlusNumberDescription(
        key="temperature_hysteresis_setting",
        name="Temperature hysteresis setting",
        endpoint="other",
        source_key="gist",
        command="change_gist",
        native_min_value=0.4,
        native_max_value=3.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer-lines",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StoutPlusNumber(coordinator, entry.entry_id, description)
        for description in NUMBERS
    )


class StoutPlusNumber(StoutPlusEntity, NumberEntity):
    """A numeric boiler setting."""

    entity_description: StoutPlusNumberDescription

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusNumberDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._endpoint = description.endpoint
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        raw_value: Any = self.coordinator.data[self.entity_description.endpoint].get(
            self.entity_description.source_key
        )
        match = re.search(r"-?\d+(?:[.,]\d+)?", str(raw_value or ""))
        return float(match.group(0).replace(",", ".")) if match else None

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.api.async_post_text(
                self.entity_description.command, f"[{value:.1f}]"
            )
        except StoutPlusApiError as err:
            raise HomeAssistantError(
                "Could not set the Stout Plus numeric value"
            ) from err
        await self.coordinator.async_request_refresh()
