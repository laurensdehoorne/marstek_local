from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import MarstekConfigEntry
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarstekLEDSwitch(entry.runtime_data)])


class MarstekLEDSwitch(MarstekEntity, SwitchEntity, RestoreEntity):
    _attr_translation_key = "led"
    _attr_assumed_state = True
    _attr_is_on: bool | None = None

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "led")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_led(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_led(False)
        self._attr_is_on = False
        self.async_write_ha_state()
