"""Sensor entities for Stout Plus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import Any, Literal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
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
    value_kind: Literal["number", "text"] = "number"


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
    StoutPlusSensorDescription(
        key="boiler_water_temperature",
        name="Boiler water temperature sensor",
        endpoint="main",
        source_key="ActValTempCarrier",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="outdoor_temperature",
        name="Outdoor temperature",
        endpoint="main",
        source_key="TempOutAir",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="dhw_temperature",
        name="Domestic hot water temperature",
        endpoint="main",
        source_key="temperatureOfDHW",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="maximum_power",
        name="Maximum power",
        endpoint="other",
        source_key="FullPwr_str",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="power_stages",
        name="Power stages",
        endpoint="other",
        source_key="PowerLevels_str",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="maximum_boiler_water_temperature",
        name="Maximum boiler water temperature",
        endpoint="other",
        source_key="SetMaxTempCarrier",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="temperature_hysteresis",
        name="Temperature hysteresis",
        endpoint="other",
        source_key="gist",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="boiler_status",
        name="Boiler status",
        endpoint="main",
        source_key="Err_str",
        value_kind="text",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="operating_mode_status",
        name="Operating mode status",
        endpoint="main",
        source_key="ModeStat",
        value_kind="text",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="anti_legionella_status",
        name="Anti-legionella status",
        endpoint="other",
        source_key="Antil_stat_str",
        value_kind="text",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="controller_firmware",
        name="Boiler controller firmware",
        endpoint="additional",
        source_key="boilerControllerSoft",
        value_kind="text",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="remote_firmware",
        name="Control panel firmware",
        endpoint="additional",
        source_key="boilerRemoteSoft",
        value_kind="text",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusSensorDescription(
        key="minimum_dhw_temperature",
        name="Minimum domestic hot water temperature",
        endpoint="additional",
        source_key="minDHWTemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="maximum_dhw_temperature",
        name="Maximum domestic hot water temperature",
        endpoint="additional",
        source_key="maxDHWTemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="minimum_pressure",
        name="Minimum pressure",
        endpoint="additional",
        source_key="MinPress",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    StoutPlusSensorDescription(
        key="maximum_pressure",
        name="Maximum pressure",
        endpoint="additional",
        source_key="MaxPress",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    StoutPlusSensorDescription(
        key="minimum_boiler_water_temperature",
        name="Minimum boiler water temperature",
        endpoint="additional",
        source_key="MinWarmCarrier",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="maximum_room_temperature",
        name="Maximum room temperature",
        endpoint="additional",
        source_key="MaxTempInRoom",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="minimum_room_temperature",
        name="Minimum room temperature",
        endpoint="additional",
        source_key="MinTempInRoom",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="sensor_1_temperature",
        name="Sensor 1 temperature",
        endpoint="additional",
        source_key="SensTemp1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="sensor_2_temperature",
        name="Sensor 2 temperature",
        endpoint="additional",
        source_key="SensTemp2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    StoutPlusSensorDescription(
        key="sensor_3_temperature",
        name="Sensor 3 temperature",
        endpoint="additional",
        source_key="SensTemp3",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=1,
    ),
    *(
        StoutPlusSensorDescription(
            key=f"sensor_{index}_mode",
            name=f"Sensor {index} mode",
            endpoint="additional",
            source_key=f"SensMode{index}",
            value_kind="text",
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for index in range(4)
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
    def native_value(self) -> float | str | None:
        raw_value: Any = self.coordinator.data[self.entity_description.endpoint].get(
            self.entity_description.source_key
        )
        if raw_value is None:
            return None

        if self.entity_description.value_kind == "text":
            value = _strip_html(str(raw_value))
            return value or None

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


def _strip_html(value: str) -> str:
    """Return readable text from the small HTML fragments used by the API."""
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", value)).split())
