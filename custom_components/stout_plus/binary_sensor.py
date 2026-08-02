"""Binary sensor entities for Stout Plus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity


@dataclass(frozen=True, kw_only=True)
class StoutPlusBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Stout Plus binary sensor."""

    endpoint: str
    source_key: str
    value_kind: Literal["connected", "rtc", "pump", "problem"]


BINARY_SENSORS: tuple[StoutPlusBinarySensorDescription, ...] = (
    StoutPlusBinarySensorDescription(
        key="outdoor_sensor_connected",
        translation_key="outdoor_sensor_connected",
        endpoint="other",
        source_key="OutAirSensor",
        value_kind="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="room_sensor_connected",
        translation_key="room_sensor_connected",
        endpoint="other",
        source_key="InAirSensor",
        value_kind="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="dhw_sensor_connected",
        translation_key="dhw_sensor_connected",
        endpoint="other",
        source_key="DomHotWatSensor",
        value_kind="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="pressure_sensor_connected",
        translation_key="pressure_sensor_connected",
        endpoint="additional",
        source_key="PressureSensor",
        value_kind="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="boiler_temperature_sensor_connected",
        translation_key="boiler_temperature_sensor_connected",
        endpoint="additional",
        source_key="OverHeatSensor",
        value_kind="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="rtc",
        translation_key="rtc",
        endpoint="other",
        source_key="RTCStatus",
        value_kind="rtc",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StoutPlusBinarySensorDescription(
        key="pump",
        translation_key="pump",
        endpoint="other",
        source_key="PmpStat",
        value_kind="pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_registry_enabled_default=False,
    ),
    StoutPlusBinarySensorDescription(
        key="problem",
        translation_key="problem",
        endpoint="main",
        source_key="Err_str",
        value_kind="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StoutPlusBinarySensor(coordinator, entry.entry_id, description)
        for description in BINARY_SENSORS
    )


class StoutPlusBinarySensor(StoutPlusEntity, BinarySensorEntity):
    """A boolean value reported by the boiler."""

    entity_description: StoutPlusBinarySensorDescription

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._endpoint = description.endpoint
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        raw_value: Any = self.coordinator.data[self.entity_description.endpoint].get(
            self.entity_description.source_key
        )
        if raw_value is None:
            return None

        value = str(raw_value)
        if self.entity_description.value_kind == "connected":
            return "Подключен" in value and "Отключен" not in value
        if self.entity_description.value_kind == "rtc":
            return "Работают" in value
        if self.entity_description.value_kind == "pump":
            try:
                status = int(raw_value)
            except (TypeError, ValueError):
                return None
            return bool(status & 0x1) if status & 0x2 else None
        main = self.coordinator.data["main"]
        error_lists = f"{main.get('Err_Lst', '')} {main.get('Err_Rel_Lst', '')}".strip()
        return bool(error_lists) or "без ошибок" not in value.lower()
