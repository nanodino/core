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
        self._stop_name: str | None = stop.get("stop_name")
        self._stop_distance: float | None = stop.get("distance")
        self._route_short_name: str | None = route.get("route_short_name")
        self._route_long_name: str | None = route.get("route_long_name")
        self._attr_unique_id = f"{entry.entry_id}_{self._stop_id}_{self._route_id}"
        self._attr_translation_placeholders = {
            "route": self._route_short_name or self._route_long_name or self._route_id,
            "stop": self._stop_name or self._stop_id,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Transit",
            name="Transit nearby departures",
        )

    def _find_next_departure(
        self,
    ) -> tuple[datetime, dict[str, Any], dict[str, Any]] | None:
        """Return (time, itinerary, schedule_item) for the earliest departure."""
        stop_data = self.coordinator.data.get(self._stop_id)
        if stop_data is None:
            return None
        best: tuple[datetime, dict[str, Any], dict[str, Any]] | None = None
        for route in stop_data["route_departures"]:
            if route.get("global_route_id") != self._route_id:
                continue
            for itinerary in route.get("itineraries", []):
                for item in itinerary.get("schedule_items", []):
                    ts = item.get("departure_time")
                    if ts is None:
                        continue
                    dt = datetime.fromtimestamp(int(ts), tz=UTC)
                    if best is None or dt < best[0]:
                        best = (dt, itinerary, item)
        return best

    @property
    def native_value(self) -> datetime | None:
        """Return the next departure time for this stop/route pair."""
        best = self._find_next_departure()
        return best[0] if best is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose route/stop/realtime info for dashboard templating."""
        attrs: dict[str, Any] = {
            "stop_name": self._stop_name,
            "stop_distance": self._stop_distance,
            "route_short_name": self._route_short_name,
            "route_long_name": self._route_long_name,
        }
        best = self._find_next_departure()
        if best is not None:
            _, itinerary, item = best
            attrs["headsign"] = itinerary.get("headsign")
            attrs["is_real_time"] = item.get("is_real_time")
        return attrs
