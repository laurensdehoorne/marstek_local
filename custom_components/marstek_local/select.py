from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .const import OPERATING_MODES
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarstekModeSelect(entry.runtime_data)])


class MarstekModeSelect(MarstekEntity, SelectEntity):
    _attr_translation_key = "operating_mode"
    _attr_options = OPERATING_MODES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "operating_mode")

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("mode_data", {}).get("mode")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_mode(option)
        await self.coordinator.async_request_refresh()
