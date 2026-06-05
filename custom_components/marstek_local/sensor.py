from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import MarstekConfigEntry
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


@dataclass(frozen=True, kw_only=True)
class MarstekSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType]


def _es(key: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: d.get(key)


def _mode(key: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: d.get("mode_data", {}).get(key)


def _bat(key: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: d.get("bat_data", {}).get(key)


def _pv(key: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: d.get("pv_data", {}).get(key)


def _energy_wh_to_kwh(key: str, sub: str | None = None) -> Callable[[dict[str, Any]], StateType]:
    """Convert Wh -> kWh, rounding to 3 decimal places."""
    def fn(d: dict[str, Any]) -> StateType:
        src = d.get(sub, d) if sub else d
        val = src.get(key)
        if val is None:
            return None
        return round(float(val) / 1000, 3)
    return fn


def _ct_energy(key: str) -> Callable[[dict[str, Any]], StateType]:
    """CT energies from ES.GetMode are raw * 0.1 = Wh -> convert to kWh."""
    def fn(d: dict[str, Any]) -> StateType:
        val = d.get("mode_data", {}).get(key)
        if val is None:
            return None
        return round(float(val) * 0.1 / 1000, 3)
    return fn


SENSORS: tuple[MarstekSensorDescription, ...] = (
    # --- Energy System (ES.GetStatus) ---
    MarstekSensorDescription(
        key="bat_soc",
        translation_key="bat_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("bat_soc"),
    ),
    MarstekSensorDescription(
        key="bat_cap",
        translation_key="bat_cap",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("bat_cap"),
    ),
    MarstekSensorDescription(
        key="bat_power",
        translation_key="bat_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("bat_power"),
    ),
    MarstekSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("pv_power"),
    ),
    MarstekSensorDescription(
        key="ongrid_power",
        translation_key="ongrid_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("ongrid_power"),
    ),
    MarstekSensorDescription(
        key="offgrid_power",
        translation_key="offgrid_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_es("offgrid_power"),
    ),
    MarstekSensorDescription(
        key="total_pv_energy",
        translation_key="total_pv_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_energy_wh_to_kwh("total_pv_energy"),
    ),
    MarstekSensorDescription(
        key="total_grid_output_energy",
        translation_key="total_grid_output_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_energy_wh_to_kwh("total_grid_output_energy"),
    ),
    MarstekSensorDescription(
        key="total_grid_input_energy",
        translation_key="total_grid_input_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_energy_wh_to_kwh("total_grid_input_energy"),
    ),
    MarstekSensorDescription(
        key="total_load_energy",
        translation_key="total_load_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_energy_wh_to_kwh("total_load_energy"),
    ),
    # --- Operating mode (ES.GetMode) ---
    MarstekSensorDescription(
        key="mode",
        translation_key="mode",
        value_fn=_mode("mode"),
    ),
    MarstekSensorDescription(
        key="ct_total_power",
        translation_key="ct_total_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_mode("total_power"),
    ),
    MarstekSensorDescription(
        key="phase_a_power",
        translation_key="phase_a_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_mode("a_power"),
    ),
    MarstekSensorDescription(
        key="phase_b_power",
        translation_key="phase_b_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_mode("b_power"),
    ),
    MarstekSensorDescription(
        key="phase_c_power",
        translation_key="phase_c_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_mode("c_power"),
    ),
    MarstekSensorDescription(
        key="ct_input_energy",
        translation_key="ct_input_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_ct_energy("input_energy"),
    ),
    MarstekSensorDescription(
        key="ct_output_energy",
        translation_key="ct_output_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_ct_energy("output_energy"),
    ),
    # --- Battery (Bat.GetStatus) ---
    MarstekSensorDescription(
        key="bat_temp",
        translation_key="bat_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_bat("bat_temp"),
    ),
    MarstekSensorDescription(
        key="bat_remaining",
        translation_key="bat_remaining",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_bat("bat_capacity"),
    ),
    MarstekSensorDescription(
        key="bat_rated",
        translation_key="bat_rated",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_bat("rated_capacity"),
    ),
    # --- PV channels (Venus D/A, Bat.GetStatus) ---
    MarstekSensorDescription(
        key="pv1_power",
        translation_key="pv1_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv1_power"),
    ),
    MarstekSensorDescription(
        key="pv1_voltage",
        translation_key="pv1_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv1_voltage"),
    ),
    MarstekSensorDescription(
        key="pv1_current",
        translation_key="pv1_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv1_current"),
    ),
    MarstekSensorDescription(
        key="pv2_power",
        translation_key="pv2_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv2_power"),
    ),
    MarstekSensorDescription(
        key="pv2_voltage",
        translation_key="pv2_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv2_voltage"),
    ),
    MarstekSensorDescription(
        key="pv2_current",
        translation_key="pv2_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv2_current"),
    ),
    MarstekSensorDescription(
        key="pv3_power",
        translation_key="pv3_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv3_power"),
    ),
    MarstekSensorDescription(
        key="pv4_power",
        translation_key="pv4_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_pv("pv4_power"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MarstekSensor(coordinator, desc) for desc in SENSORS
    )


class MarstekSensor(MarstekEntity, SensorEntity):
    entity_description: MarstekSensorDescription

    def __init__(
        self,
        coordinator: MarstekCoordinator,
        description: MarstekSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)
