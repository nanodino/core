"""Test the transitapp setup flow."""

from http import HTTPStatus

from aiohttp import ClientError

from homeassistant.components.transitapp.const import API_URL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import HomeAssistant

from .conftest import NEARBY_STOPS_RESPONSE, STOP_DEPARTURES_RESPONSE

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

NEARBY_URL = f"{API_URL}/public/nearby_stops"
DEPARTURES_URL = f"{API_URL}/public/stop_departures"


def _mock_successful_api(aioclient_mock: AiohttpClientMocker) -> None:
    """Mock the two endpoints the coordinator polls."""
    aioclient_mock.get(NEARBY_URL, status=HTTPStatus.OK, json=NEARBY_STOPS_RESPONSE)
    aioclient_mock.get(
        DEPARTURES_URL, status=HTTPStatus.OK, json=STOP_DEPARTURES_RESPONSE
    )


def _count(aioclient_mock: AiohttpClientMocker, path: str) -> int:
    return len([c for c in aioclient_mock.mock_calls if c[1].path == path])


async def test_setup_and_unload(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """The integration sets up and unloads cleanly."""
    _mock_successful_api(aioclient_mock)
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data is not None

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_on_connection_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A transient API error marks the entry for retry, not failure."""
    aioclient_mock.get(NEARBY_URL, exc=ClientError)
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_failure(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A 401 from the API puts the entry into SETUP_ERROR (auth failure)."""
    aioclient_mock.get(NEARBY_URL, status=HTTPStatus.UNAUTHORIZED)
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_location_change_refetches_stops(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A core_config_updated event with new lat/lon triggers nearby_stops re-fetch."""
    _mock_successful_api(aioclient_mock)
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert _count(aioclient_mock, "/v3/public/nearby_stops") == 1
    assert _count(aioclient_mock, "/v3/public/stop_departures") == 1

    hass.config.latitude += 0.01
    hass.config.longitude += 0.01
    hass.bus.async_fire(EVENT_CORE_CONFIG_UPDATE)
    await hass.async_block_till_done()

    assert _count(aioclient_mock, "/v3/public/nearby_stops") == 2
    assert _count(aioclient_mock, "/v3/public/stop_departures") == 2


async def test_unchanged_location_does_not_refetch(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A core_config_updated event with the same lat/lon does nothing."""
    _mock_successful_api(aioclient_mock)
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_CORE_CONFIG_UPDATE)
    await hass.async_block_till_done()

    assert _count(aioclient_mock, "/v3/public/nearby_stops") == 1
    assert _count(aioclient_mock, "/v3/public/stop_departures") == 1
