"""Refresh button for transitapp."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TransitAppConfigEntry
from .const import DOMAIN
from .coordinator import TransitAppCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TransitAppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the refresh button."""
    async_add_entities([RefreshButton(entry.runtime_data, entry)])


class RefreshButton(CoordinatorEntity[TransitAppCoordinator], ButtonEntity):
    """Force a re-poll of departures."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"

    def __init__(
        self, coordinator: TransitAppCoordinator, entry: TransitAppConfigEntry
    ) -> None:
        """Initialise the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Transit",
            name="Transit nearby departures",
        )

    async def async_press(self) -> None:
        """Trigger an immediate coordinator refresh."""
        await self.coordinator.async_request_refresh()
