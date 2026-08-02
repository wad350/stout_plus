"""Sensor entities for Stout Plus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity


@dataclass(frozen=True, kw_only=True)
class StoutPlusSensorDescription(SensorEntityDescription):
    """Describe a Stout Plus sensor."""

    endpoint: str
    source_key: str
    precision: int | None = None


SENSORS: tuple[StoutPlusSensorDescription, ...] = (
    StoutPlusSensorDescription(
        key="power",
        name="Power consumption",
        endpoint="other",
        source_key="CurrPwr_str",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    StoutPlusSensorDescription(
        key="pressure",
        name="Pressure",
        endpoint="other",
        source_key="ActPress",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    StoutPlusSensorDescription(
        key="room_temp",
        name="Room temperature sensor",
        endpoint="additional",
        source_key="SensTemp0",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StoutPlusSensor(coordinator, entry.entry_id, description)
        for description in SENSORS
    )


class StoutPlusSensor(StoutPlusEntity, SensorEntity):
    """A numeric value reported by the boiler."""

    entity_description: StoutPlusSensorDescription

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusSensorDescription,
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
        if raw_value is None:
            return None

        match = re.search(r"-?\d+(?:[.,]\d+)?", str(raw_value))
        if match is None:
            return None
        try:
            value = float(match.group(0).replace(",", "."))
        except ValueError:
            return None
        if self.entity_description.precision is not None:
            return round(value, self.entity_description.precision)
        return value
