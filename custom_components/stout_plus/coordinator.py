"""Data coordinator for the Stout Plus integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StoutPlusApi, StoutPlusApiError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class StoutPlusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all boiler endpoints once per update cycle."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: StoutPlusApi
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        endpoint_names = ("main", "other", "additional")
        results = await asyncio.gather(
            self.api.async_get("main_params"),
            self.api.async_get("other_params"),
            self.api.async_get("additional_params"),
            return_exceptions=True,
        )

        data: dict[str, Any] = {"_available": set()}
        errors: list[StoutPlusApiError] = []
        for name, result in zip(endpoint_names, results, strict=True):
            if isinstance(result, StoutPlusApiError):
                data[name] = {}
                errors.append(result)
            else:
                data[name] = result
                data["_available"].add(name)

        if len(errors) == len(endpoint_names):
            raise UpdateFailed(f"Error communicating with boiler: {errors[0]}")
        return data

    def endpoint_available(self, endpoint: str) -> bool:
        """Return whether an endpoint succeeded in the latest update."""
        return endpoint in self.data.get("_available", set())
