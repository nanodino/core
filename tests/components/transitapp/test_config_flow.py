"""Test the transitapp config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.components.transitapp.const import (
    API_URL,
    CONF_RADIUS,
    DOMAIN,
    PROBE_PATH,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import TEST_API_KEY, TEST_RADIUS

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

PROBE_URL = f"{API_URL}{PROBE_PATH}"


async def test_full_flow(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the form creates an entry when the API key is valid."""
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.OK, json={})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Transit"
    assert result["data"] == {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_invalid_auth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the flow surfaces invalid_auth when the API rejects the key."""
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.UNAUTHORIZED)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.OK, json={})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_cannot_connect(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the flow surfaces cannot_connect when the network errors."""
    aioclient_mock.get(PROBE_URL, exc=ClientError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.OK, json={})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_unknown_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the flow surfaces ``unknown`` for unexpected HTTP errors."""
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unexpected_exception(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the flow surfaces ``unknown`` for unexpected exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.transitapp.config_flow.TransitAppClient.async_probe",
        side_effect=RuntimeError("boom"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}

    aioclient_mock.get(PROBE_URL, status=HTTPStatus.OK, json={})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(mock_setup_entry.mock_calls) == 1


async def test_duplicate_entry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that adding a second entry with the same API key aborts."""
    mock_config_entry.add_to_hass(hass)
    aioclient_mock.get(PROBE_URL, status=HTTPStatus.OK, json={})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY, CONF_RADIUS: TEST_RADIUS},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
