"""Switch entities for Stout Plus."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up switch entities."""
    coordinator: StoutPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        (
            StoutPlusDhwSwitch(coordinator, entry.entry_id),
            StoutPlusAntiLegionellaSwitch(coordinator, entry.entry_id),
        )
    )


class StoutPlusSwitch(StoutPlusEntity, SwitchEntity):
    """Base class for a writable boiler switch."""

    async def _async_write(self, enabled: bool) -> None:
        raise NotImplementedError

    async def async_turn_on(self, **kwargs: object) -> None:
        try:
            await self._async_write(True)
        except StoutPlusApiError as err:
            raise HomeAssistantError("Could not enable the Stout Plus option") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        try:
            await self._async_write(False)
        except StoutPlusApiError as err:
            raise HomeAssistantError("Could not disable the Stout Plus option") from err
        await self.coordinator.async_request_refresh()


class StoutPlusDhwSwitch(StoutPlusSwitch):
    """Enable domestic hot water heating."""

    _attr_translation_key = "domestic_hot_water"
    _attr_icon = "mdi:water-boiler"
    _endpoint = "main"

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_dhw"

    @property
    def is_on(self) -> bool | None:
        try:
            return bool(int(self.coordinator.data["main"]["settedDHWmode"]))
        except (KeyError, TypeError, ValueError):
            return None

    async def _async_write(self, enabled: bool) -> None:
        await self.coordinator.api.async_post_text("switch_dhw", f"[{int(enabled)}]")


class StoutPlusAntiLegionellaSwitch(StoutPlusSwitch):
    """Enable the anti-legionella cycle."""

    _attr_translation_key = "anti_legionella"
    _attr_icon = "mdi:bacteria-outline"
    _endpoint = "other"

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_anti_legionella"

    @property
    def is_on(self) -> bool | None:
        try:
            return bool(int(self.coordinator.data["other"]["Antil_trn"]))
        except (KeyError, TypeError, ValueError):
            return None

    async def _async_write(self, enabled: bool) -> None:
        await self.coordinator.api.async_post_form(
            "apply_alig_page",
            {"Antil_trn": "Включен" if enabled else "Выключен"},
        )
