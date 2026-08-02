"""Power limit selects for Stout Plus."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import StoutPlusApiError
from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity

POWER_OPTIONS = ["1.5", "3.0", "4.5", "6.0", "7.5", "9.0"]


@dataclass(frozen=True, kw_only=True)
class StoutPlusSelectDescription(SelectEntityDescription):
    """Describe a Stout Plus select."""

    source_key: str
    icon: str


SELECTS: tuple[StoutPlusSelectDescription, ...] = (
    StoutPlusSelectDescription(
        key="power_day",
        name="Day power limit",
        source_key="amountActiveLevelsPerDay",
        icon="mdi:flash",
    ),
    StoutPlusSelectDescription(
        key="power_night",
        name="Night power limit",
        source_key="amountActiveLevelsAtNight",
        icon="mdi:weather-night",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StoutPlusPowerSelect(coordinator, entry.entry_id, description)
        for description in SELECTS
    )


class StoutPlusPowerSelect(StoutPlusEntity, SelectEntity):
    """Select the maximum boiler power in kW."""

    _attr_options = POWER_OPTIONS
    _endpoint = "other"
    entity_description: StoutPlusSelectDescription

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusSelectDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"

    @property
    def current_option(self) -> str | None:
        try:
            stages = int(
                self.coordinator.data["other"][self.entity_description.source_key]
            )
        except (KeyError, TypeError, ValueError):
            return None
        option = f"{stages * 1.5:.1f}"
        return option if option in self.options else None

    async def async_select_option(self, option: str) -> None:
        """Set a power limit in kW.

        The boiler accepts kW in the form but reports the resulting number of
        active 1.5 kW stages from ``other_params``.
        """
        try:
            await self.coordinator.api.async_post_form(
                "apply_power_day",
                {self.entity_description.source_key: option},
            )
        except StoutPlusApiError as err:
            raise HomeAssistantError(
                "Could not set the Stout Plus power limit"
            ) from err
        await self.coordinator.async_request_refresh()
