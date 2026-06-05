from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import MarstekConfigEntry
from .const import DOD_MAX, DOD_MIN
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarstekDODNumber(entry.runtime_data)])


class MarstekDODNumber(MarstekEntity, NumberEntity, RestoreEntity):
    _attr_translation_key = "dod"
    _attr_native_min_value = DOD_MIN
    _attr_native_max_value = DOD_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "%"
    _attr_native_value: float | None = None

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dod")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.set_dod(int(value))
        self._attr_native_value = value
        self.async_write_ha_state()
