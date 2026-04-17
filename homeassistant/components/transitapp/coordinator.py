"""Data update coordinator for the transitapp integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TransitAppAuthError,
    TransitAppClient,
    TransitAppConnectionError,
    TransitAppError,
)
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type StopData = dict[str, Any]


class TransitAppCoordinator(DataUpdateCoordinator[dict[str, StopData]]):
    """Polls departures every UPDATE_INTERVAL.

    Nearby stops are refreshed only when the home location changes (or on first run).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: TransitAppClient,
        latitude: float,
        longitude: float,
        radius_meters: int,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=UPDATE_INTERVAL,
        )
        self._client = client
        self._latitude = latitude
        self._longitude = longitude
        self._radius = radius_meters
        self._stops: dict[str, dict[str, Any]] | None = None

    @property
    def location(self) -> tuple[float, float]:
        """Return the cached home location."""
        return (self._latitude, self._longitude)

    def update_location(self, latitude: float, longitude: float) -> None:
        """Replace the home location and invalidate the cached nearby stops."""
        self._latitude = latitude
        self._longitude = longitude
        self._stops = None

    async def _async_update_data(self) -> dict[str, StopData]:
        """Fetch nearby stops on first run/location change, then batch departures."""
        try:
            if self._stops is None:
                nearby = await self._client.async_nearby_stops(
                    self._latitude, self._longitude, self._radius
                )
                self._stops = {
                    stop["global_stop_id"]: stop for stop in nearby.get("stops", [])
                }

            if not self._stops:
                return {}

            departures = await self._client.async_stop_departures(
                list(self._stops.keys())
            )
        except TransitAppAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (TransitAppConnectionError, TransitAppError) as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, StopData] = {
            stop_id: {"stop": stop, "route_departures": []}
            for stop_id, stop in self._stops.items()
        }
        for route in departures.get("route_departures", []):
            stop_id = route.get("global_stop_id")
            if stop_id in result:
                result[stop_id]["route_departures"].append(route)
        return result
