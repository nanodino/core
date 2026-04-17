"""Common fixtures for the transitapp tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.transitapp.const import CONF_RADIUS, DOMAIN
from homeassistant.const import CONF_API_KEY

from tests.common import MockConfigEntry

TEST_API_KEY = "test-api-key"
TEST_RADIUS = 500


NEARBY_STOPS_RESPONSE = {
    "stops": [
        {
            "global_stop_id": "stop-1",
            "stop_name": "Main St & 1st Ave",
            "distance": 120,
        }
    ]
}

STOP_DEPARTURES_RESPONSE = {
    "route_departures": [
        {
            "global_stop_id": "stop-1",
            "global_route_id": "route-a",
            "route_short_name": "10",
            "route_long_name": "Downtown Express",
            "itineraries": [
                {
                    "headsign": "Downtown",
                    "schedule_items": [
                        {"departure_time": 1_900_000_000, "is_real_time": True}
                    ],
                }
            ],
        },
        {
            "global_stop_id": "stop-1",
            "global_route_id": "route-b",
            "route_short_name": "55",
            "route_long_name": "Crosstown",
            "itineraries": [
                {
                    "headsign": "Uptown",
                    "schedule_items": [
                        {"departure_time": 1_900_000_300, "is_real_time": False}
                    ],
                }
            ],
        },
    ]
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.transitapp.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry for transitapp."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Transit",
        data={CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )
