"""The transitapp integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TransitAppClient
from .const import CONF_RADIUS
from .coordinator import TransitAppCoordinator

_PLATFORMS: list[Platform] = [Platform.SENSOR]

type TransitAppConfigEntry = ConfigEntry[TransitAppCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TransitAppConfigEntry) -> bool:
    """Set up transitapp from a config entry."""
    client = TransitAppClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    coordinator = TransitAppCoordinator(
        hass,
        entry,
        client,
        hass.config.latitude,
        hass.config.longitude,
        entry.data[CONF_RADIUS],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TransitAppConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
