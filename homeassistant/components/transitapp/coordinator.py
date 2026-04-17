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
    """Polls nearby stops and per-stop departures from Transit."""

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

    async def _async_update_data(self) -> dict[str, StopData]:
        """Fetch nearby stops and their departures."""
        try:
            nearby = await self._client.async_nearby_stops(
                self._latitude, self._longitude, self._radius
            )
            result: dict[str, StopData] = {}
            for stop in nearby.get("stops", []):
                stop_id = stop["global_stop_id"]
                departures = await self._client.async_stop_departures(stop_id)
                result[stop_id] = {"stop": stop, "departures": departures}
        except TransitAppAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (TransitAppConnectionError, TransitAppError) as err:
            raise UpdateFailed(str(err)) from err
        return result
