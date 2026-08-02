"""Common entity helpers for Stout Plus."""

from __future__ import annotations

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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Stout Plus boiler",
            manufacturer="Stout",
            model="Stout Plus 9 kW",
            configuration_url=f"http://{coordinator.api.host}",
        )

    @property
    def available(self) -> bool:
        """Return availability of the entity's source endpoint."""
        return super().available and (
            self._endpoint is None
            or self.coordinator.endpoint_available(self._endpoint)
        )
