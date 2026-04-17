"""Test the transitapp refresh button."""

from http import HTTPStatus

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.transitapp.const import API_URL
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from .conftest import NEARBY_STOPS_RESPONSE, STOP_DEPARTURES_RESPONSE

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

NEARBY_URL = f"{API_URL}/public/nearby_stops"
DEPARTURES_URL = f"{API_URL}/public/stop_departures"


async def test_refresh_button_triggers_poll(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Pressing the refresh button issues an additional departures poll."""
    aioclient_mock.get(NEARBY_URL, status=HTTPStatus.OK, json=NEARBY_STOPS_RESPONSE)
    aioclient_mock.get(
        DEPARTURES_URL, status=HTTPStatus.OK, json=STOP_DEPARTURES_RESPONSE
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    departures_calls_before = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if c[1].path == "/v3/public/stop_departures"
        ]
    )

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.transit_nearby_departures_refresh_departures"},
        blocking=True,
    )

    departures_calls_after = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if c[1].path == "/v3/public/stop_departures"
        ]
    )
    assert departures_calls_after == departures_calls_before + 1
