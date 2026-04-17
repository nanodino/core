"""Thin async client for the Transit public API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

from .const import API_KEY_HEADER, API_URL, PROBE_PATH


class TransitAppError(Exception):
    """Base exception for Transit API errors."""


class TransitAppAuthError(TransitAppError):
    """Raised when the API key is rejected."""


class TransitAppConnectionError(TransitAppError):
    """Raised when the Transit API cannot be reached."""


class TransitAppClient:
    """Minimal client hitting the Transit public API."""

    def __init__(self, session: ClientSession, api_key: str) -> None:
        """Store the session and API key."""
        self._session = session
        self._api_key = api_key

    async def async_probe(self) -> None:
        """Hit a lightweight endpoint to verify the API key is valid."""
        await self._async_get(f"{API_URL}{PROBE_PATH}")

    async def async_nearby_stops(
        self, latitude: float, longitude: float, max_distance: int
    ) -> dict[str, Any]:
        """Return stops within ``max_distance`` metres of the coordinates."""
        return await self._async_get(
            f"{API_URL}/public/nearby_stops",
            params={
                "lat": latitude,
                "lon": longitude,
                "max_distance": max_distance,
            },
        )

    async def async_stop_departures(self, global_stop_ids: list[str]) -> dict[str, Any]:
        """Return upcoming departures for one or more stops in a single call."""
        return await self._async_get(
            f"{API_URL}/public/stop_departures",
            params={"global_stop_ids": ",".join(global_stop_ids)},
        )

    async def _async_get(
        self, url: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform an authenticated GET and return JSON."""
        try:
            response = await self._session.get(
                url,
                headers={API_KEY_HEADER: self._api_key},
                params=params,
            )
        except ClientError as err:
            raise TransitAppConnectionError from err

        if response.status in (401, 403):
            raise TransitAppAuthError(f"HTTP {response.status} from {url}")
        if response.status >= 400:
            body = await response.text()
            raise TransitAppConnectionError(
                f"HTTP {response.status} from {url}: {body[:200]}"
            )

        return await response.json()
