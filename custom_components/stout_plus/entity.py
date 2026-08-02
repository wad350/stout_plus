"""Common entity helpers for Stout Plus."""

from __future__ import annotations

import re

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StoutPlusCoordinator


class StoutPlusEntity(CoordinatorEntity[StoutPlusCoordinator]):
    """Base class for entities belonging to one boiler."""

    _attr_has_entity_name = True
    _endpoint: str | None = None

    def __init__(self, coordinator: StoutPlusCoordinator, entry_id: str) -> None:
        """Initialize a boiler entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        full_power = coordinator.data.get("main", {}).get("FullPwr_str")
        model = "Stout Plus"
        try:
            model = f"Stout Plus {float(full_power):g} kW"
        except (TypeError, ValueError):
            pass

        firmware = coordinator.data.get("additional", {}).get(
            "boilerControllerSoft", ""
        )
        firmware_match = re.search(r"\d+(?:\.\d+)+", str(firmware))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Stout Plus boiler",
            manufacturer="Stout",
            model=model,
            sw_version=firmware_match.group(0) if firmware_match else None,
            configuration_url=f"http://{coordinator.api.host}",
        )

    @property
    def available(self) -> bool:
        """Return availability of the entity's source endpoint."""
        return super().available and (
            self._endpoint is None
            or self.coordinator.endpoint_available(self._endpoint)
        )
