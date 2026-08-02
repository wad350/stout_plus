"""Power limit selects for Stout Plus."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import StoutPlusApiError
from .const import DOMAIN
from .coordinator import StoutPlusCoordinator
from .entity import StoutPlusEntity

POWER_OPTIONS = ["1.5", "3.0", "4.5", "6.0", "7.5", "9.0"]


@dataclass(frozen=True, kw_only=True)
class StoutPlusIndexSelectDescription(SelectEntityDescription):
    """Describe a select whose API value is an option index."""

    endpoint: str
    source_key: str
    command: str
    options: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class StoutPlusFormSelectDescription(SelectEntityDescription):
    """Describe an index setting submitted as a form value."""

    source_key: str
    command: str
    options: tuple[str, ...]
    payload_values: tuple[str, ...]
    index_mask: int | None = None


INDEX_SELECTS: tuple[StoutPlusIndexSelectDescription, ...] = (
    StoutPlusIndexSelectDescription(
        key="operating_mode",
        translation_key="operating_mode",
        endpoint="main",
        source_key="setMode",
        command="switch_mode",
        options=(
            "heating",
            "weekly_schedule",
            "room_temperature",
            "outdoor_curve",
            "antifreeze",
        ),
        icon="mdi:radiator",
    ),
    StoutPlusIndexSelectDescription(
        key="outdoor_curve",
        translation_key="outdoor_curve",
        endpoint="main",
        source_key="SetDepNumber",
        command="change_outtrg",
        options=("22", "25", "30", "35", "40", "45", "50", "55", "60"),
        icon="mdi:chart-bell-curve-cumulative",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusIndexSelectDescription(
        key="external_management",
        translation_key="external_management",
        endpoint="other",
        source_key="exManagMode",
        command="switch_manage",
        options=("disabled", "opentherm", "thermostat"),
        icon="mdi:connection",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusIndexSelectDescription(
        key="remote_control_source",
        translation_key="remote_control_source",
        endpoint="other",
        source_key="srcMQTT",
        command="mqtt_rem_src",
        options=("application", "telegram"),
        icon="mdi:remote",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusIndexSelectDescription(
        key="warning_sound",
        translation_key="warning_sound",
        endpoint="other",
        source_key="warn",
        command="switch_voice",
        options=("off", "on"),
        icon="mdi:volume-high",
        entity_category=EntityCategory.CONFIG,
    ),
)


FORM_SELECTS: tuple[StoutPlusFormSelectDescription, ...] = (
    StoutPlusFormSelectDescription(
        key="anti_legionella_temperature",
        translation_key="anti_legionella_temperature",
        source_key="Antil_temp",
        command="apply_alig_page",
        options=("60_c", "70_c"),
        payload_values=("60°C", "70°C"),
        icon="mdi:thermometer-high",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusFormSelectDescription(
        key="anti_legionella_weekday",
        translation_key="anti_legionella_weekday",
        source_key="Antil_wday_str",
        command="apply_alig_page",
        options=(
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ),
        payload_values=(
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ),
        icon="mdi:calendar-week",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusFormSelectDescription(
        key="pump_overrun",
        translation_key="pump_overrun",
        source_key="PumpLag",
        command="apply_other_page",
        options=("continuous", "minutes_5", "minutes_10", "minutes_15"),
        payload_values=(
            "Постоянная работа",
            "выбег 5 мин",
            "выбег 10 мин",
            "выбег 15 мин",
        ),
        index_mask=0x7F,
        icon="mdi:pump",
        entity_category=EntityCategory.CONFIG,
    ),
)


@dataclass(frozen=True, kw_only=True)
class StoutPlusSelectDescription(SelectEntityDescription):
    """Describe a Stout Plus select."""

    source_key: str
    icon: str


SELECTS: tuple[StoutPlusSelectDescription, ...] = (
    StoutPlusSelectDescription(
        key="power_day",
        translation_key="power_day",
        source_key="amountActiveLevelsPerDay",
        icon="mdi:flash",
        entity_category=EntityCategory.CONFIG,
    ),
    StoutPlusSelectDescription(
        key="power_night",
        translation_key="power_night",
        source_key="amountActiveLevelsAtNight",
        icon="mdi:weather-night",
        entity_category=EntityCategory.CONFIG,
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
        [
            *(
                StoutPlusPowerSelect(coordinator, entry.entry_id, description)
                for description in SELECTS
            ),
            *(
                StoutPlusIndexSelect(coordinator, entry.entry_id, description)
                for description in INDEX_SELECTS
            ),
            *(
                StoutPlusFormSelect(coordinator, entry.entry_id, description)
                for description in FORM_SELECTS
            ),
            StoutPlusDhwPowerSelect(coordinator, entry.entry_id),
        ]
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


class StoutPlusIndexSelect(StoutPlusEntity, SelectEntity):
    """Select an API option represented by its zero-based index."""

    entity_description: StoutPlusIndexSelectDescription

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusIndexSelectDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._endpoint = description.endpoint
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_options = list(description.options)

    @property
    def current_option(self) -> str | None:
        try:
            index = int(
                self.coordinator.data[self.entity_description.endpoint][
                    self.entity_description.source_key
                ]
            )
            return self.options[index]
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        try:
            index = self.options.index(option)
            await self.coordinator.api.async_post_text(
                self.entity_description.command, f"[{index}]"
            )
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError("Could not set the Stout Plus option") from err
        await self.coordinator.async_request_refresh()


class StoutPlusDhwPowerSelect(StoutPlusEntity, SelectEntity):
    """Select the domestic hot water heating power."""

    _attr_translation_key = "dhw_power"
    _attr_icon = "mdi:water-boiler"
    _endpoint = "main"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_dhw_power"

    @property
    def options(self) -> list[str]:
        try:
            stages = int(self.coordinator.data["main"]["PowerLevels_str"])
            full_power = float(self.coordinator.data["main"]["FullPwr_str"])
        except (KeyError, TypeError, ValueError):
            return []
        return [f"{full_power / stages * index:.1f}" for index in range(1, stages + 1)]

    @property
    def current_option(self) -> str | None:
        try:
            level = int(self.coordinator.data["main"]["DHWLevel"])
            return self.options[level - 1]
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        try:
            index = self.options.index(option)
            await self.coordinator.api.async_post_text("change_pwrlst", f"[{index}]")
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(
                "Could not set the Stout Plus domestic hot water power"
            ) from err
        await self.coordinator.async_request_refresh()


class StoutPlusFormSelect(StoutPlusEntity, SelectEntity):
    """Select a form-backed boiler option."""

    entity_description: StoutPlusFormSelectDescription
    _endpoint = "other"

    def __init__(
        self,
        coordinator: StoutPlusCoordinator,
        entry_id: str,
        description: StoutPlusFormSelectDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_options = list(description.options)

    @property
    def current_option(self) -> str | None:
        try:
            index = int(
                self.coordinator.data["other"][self.entity_description.source_key]
            )
            if self.entity_description.index_mask is not None:
                index &= self.entity_description.index_mask
            return self.options[index]
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        try:
            index = self.options.index(option)
            await self.coordinator.api.async_post_form(
                self.entity_description.command,
                {
                    self.entity_description.source_key: (
                        self.entity_description.payload_values[index]
                    )
                },
            )
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(
                "Could not set the Stout Plus form option"
            ) from err
        await self.coordinator.async_request_refresh()
