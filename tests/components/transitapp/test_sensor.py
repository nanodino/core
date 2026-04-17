"""Test the transitapp sensor platform."""

from datetime import UTC, datetime
from http import HTTPStatus

from homeassistant.components.transitapp.const import API_URL
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import NEARBY_STOPS_RESPONSE, STOP_DEPARTURES_RESPONSE

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

NEARBY_URL = f"{API_URL}/public/nearby_stops"
DEPARTURES_URL = f"{API_URL}/public/stop_departures"


async def test_sensor_entities(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """One sensor per (stop, route) is created with the correct state."""
    aioclient_mock.get(NEARBY_URL, status=HTTPStatus.OK, json=NEARBY_STOPS_RESPONSE)
    aioclient_mock.get(
        DEPARTURES_URL, status=HTTPStatus.OK, json=STOP_DEPARTURES_RESPONSE
    )
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entries) == 2
    assert {e.unique_id for e in entries} == {
        f"{mock_config_entry.entry_id}_stop-1_route-a",
        f"{mock_config_entry.entry_id}_stop-1_route-b",
    }

    state_a = hass.states.get(
        entity_registry.async_get_entity_id(
            "sensor",
            "transitapp",
            f"{mock_config_entry.entry_id}_stop-1_route-a",
        )
    )
    assert state_a is not None
    assert state_a.state != STATE_UNAVAILABLE
    assert datetime.fromisoformat(state_a.state) == datetime.fromtimestamp(
        1_900_000_000, tz=UTC
    )
