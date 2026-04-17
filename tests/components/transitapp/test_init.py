"""Test the transitapp setup flow."""

from http import HTTPStatus

from aiohttp import ClientError

from homeassistant.components.transitapp.const import API_URL
from homeassistant.config_entries import ConfigEntryState
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
