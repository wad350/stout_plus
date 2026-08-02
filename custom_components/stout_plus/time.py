"""Day/night schedule entities for Stout Plus."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import StoutPlusApiError
from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity


@dataclass(frozen=True, kw_only=True)
class StoutPlusTimeDescription(TimeEntityDescription):
    """Describe a Stout Plus time value."""

    source_key: str
    icon: str
    command: str = "apply_power_day"
    hour_only: bool = False


TIME_ENTITIES: tuple[StoutPlusTimeDescription, ...] = (
    StoutPlusTimeDescription(
        key="night_time",
        translation_key="night_time",
        source_key="nightTime",
        icon="mdi:timer-settings-outline",
    ),
    StoutPlusTimeDescription(
        key="day_time",
        translation_key="day_time",
        source_key="dayTime",
        icon="mdi:timer-settings",
    ),
    StoutPlusTimeDescription(
        key="anti_legionella_time",
        translation_key="anti_legionella_time",
        source_key="set_time_legionella",
        icon="mdi:bacteria-outline",
        command="apply_alig_page",
        hour_only=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up time entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StoutPlusTime(coordinator, entry.entry_id, description)
        for description in TIME_ENTITIES
    )


class StoutPlusTime(StoutPlusEntity, TimeEntity):
    """A day/night schedule boundary."""

    entity_description: StoutPlusTimeDescription
    _endpoint = "other"

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusTimeDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"

    @property
    def native_value(self) -> time | None:
        value = self.coordinator.data["other"].get(self.entity_description.source_key)
        try:
            if self.entity_description.hour_only:
                return time(hour=int(value))
            return time.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    async def async_set_value(self, value: time) -> None:
        try:
            await self.coordinator.api.async_post_form(
                self.entity_description.command,
                {
                    self.entity_description.source_key: (
                        str(value.hour)
                        if self.entity_description.hour_only
                        else value.strftime("%H:%M")
                    )
                },
            )
        except StoutPlusApiError as err:
            raise HomeAssistantError("Could not set the Stout Plus schedule") from err
        await self.coordinator.async_request_refresh()
