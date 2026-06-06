from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import MarstekConfigEntry
from .const import DOD_MAX, DOD_MIN
from .entity import MarstekEntity

PASSIVE_POWER_MIN = -5000
PASSIVE_POWER_MAX = 5000
PASSIVE_POWER_STEP = 10

PASSIVE_DURATION_MIN = 0
PASSIVE_DURATION_MAX = 86400  # 24 h
PASSIVE_DURATION_STEP = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            MarstekDODNumber(coordinator),
            MarstekPassivePowerNumber(coordinator),
            MarstekPassiveDurationNumber(coordinator),
        ]
    )


class MarstekDODNumber(MarstekEntity, NumberEntity, RestoreEntity):
    """Depth of discharge setting (30–88 %)."""

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


class MarstekPassivePowerNumber(MarstekEntity, NumberEntity, RestoreEntity):
    """Passive-mode power target.

    Setting this immediately activates Passive mode at the given wattage.
    Positive = charge, negative = discharge (verify sign with your hardware).
    Set to 0 to idle without charging or discharging.
    """

    _attr_translation_key = "passive_power"
    _attr_native_min_value = PASSIVE_POWER_MIN
    _attr_native_max_value = PASSIVE_POWER_MAX
    _attr_native_step = PASSIVE_POWER_STEP
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_value: float | None = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "passive_power")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                val = float(last_state.state)
                self._attr_native_value = val
                self.coordinator.client._passive_power = int(val)
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Send Passive mode command with new power; uses current stored duration."""
        await self.coordinator.client.set_passive(power=int(value))
        self._attr_native_value = value
        self.async_write_ha_state()
        # Refresh so the mode sensor picks up "Passive"
        await self.coordinator.async_request_refresh()


class MarstekPassiveDurationNumber(MarstekEntity, NumberEntity, RestoreEntity):
    """Passive-mode countdown timer (0 = run indefinitely)."""

    _attr_translation_key = "passive_duration"
    _attr_native_min_value = PASSIVE_DURATION_MIN
    _attr_native_max_value = PASSIVE_DURATION_MAX
    _attr_native_step = PASSIVE_DURATION_STEP
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_value: float | None = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "passive_duration")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                val = float(last_state.state)
                self._attr_native_value = val
                self.coordinator.client._passive_duration = int(val)
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Store the duration locally — takes effect next time passive power is set."""
        self.coordinator.client._passive_duration = int(value)
        self._attr_native_value = value
        self.async_write_ha_state()
