"""Next-departure sensors for transitapp."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TransitAppConfigEntry
from .const import DOMAIN
from .coordinator import TransitAppCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TransitAppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one sensor per (stop, route) discovered at first refresh."""
    coordinator = entry.runtime_data
    async_add_entities(
        NextDepartureSensor(coordinator, entry, stop_data["stop"], route)
        for stop_data in coordinator.data.values()
        for route in stop_data["route_departures"]
    )


class NextDepartureSensor(CoordinatorEntity[TransitAppCoordinator], SensorEntity):
    """Next scheduled departure for a given route at a given stop."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "next_departure"

    def __init__(
        self,
        coordinator: TransitAppCoordinator,
        entry: TransitAppConfigEntry,
        stop: dict[str, Any],
        route: dict[str, Any],
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._stop_id: str = stop["global_stop_id"]
        self._route_id: str = route["global_route_id"]
        self._attr_unique_id = f"{entry.entry_id}_{self._stop_id}_{self._route_id}"
        self._attr_translation_placeholders = {
            "route": (
                route.get("route_short_name")
                or route.get("route_long_name")
                or self._route_id
            ),
            "stop": stop.get("stop_name") or self._stop_id,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Transit",
            name="Transit nearby departures",
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the next departure time for this stop/route pair."""
        stop_data = self.coordinator.data.get(self._stop_id)
        if stop_data is None:
            return None
        for route in stop_data["route_departures"]:
            if route.get("global_route_id") != self._route_id:
                continue
            for itinerary in route.get("itineraries", []):
                for item in itinerary.get("schedule_items", []):
                    ts = item.get("departure_time")
                    if ts is not None:
                        return datetime.fromtimestamp(int(ts), tz=UTC)
        return None
