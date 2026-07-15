"""Tests for typed simulation-state errors introduced in D-EH5."""

from types import MethodType

import pytest

from dibs_computing_core.iso_simulator.exceptions import (
    SimulationStateError,
    ThermalCalculationError,
)
from dibs_computing_core.iso_simulator.model.building import Building
from dibs_computing_core.iso_simulator.supply_system import HeatPumpAirSource


def test_heat_pump_without_demand_raises_simulation_state_error():
    heat_pump = HeatPumpAirSource(0, 10, 35, 12, False, False)

    with pytest.raises(SimulationStateError) as raised:
        heat_pump.calc_loads()

    assert raised.value.phase == "simulate_hours"
    assert raised.value.context == {
        "has_heating_demand": False,
        "has_cooling_demand": False,
    }


def test_energy_demand_without_demand_flag_raises_simulation_state_error():
    building = Building.__new__(Building)
    building.has_heating_demand = False
    building.has_cooling_demand = False
    building.calc_temperatures_crank_nicolson = MethodType(
        lambda self, *args: (0.0, 20.0, 20.0), building
    )

    with pytest.raises(SimulationStateError) as raised:
        building.calc_energy_demand(0.0, 0.0, 10.0, 20.0)

    assert raised.value.context == {
        "has_heating_demand": False,
        "has_cooling_demand": False,
    }


def test_invalid_thermal_result_raises_thermal_calculation_error():
    building = Building.__new__(Building)
    building.has_heating_demand = True
    building.has_cooling_demand = False
    building.t_set_heating = 20.0
    building._energy_floor_ax10 = 100.0
    building.max_heating_energy = 1000.0
    building.max_cooling_energy = -1000.0
    building.calc_temperatures_crank_nicolson = MethodType(
        lambda self, *args: (0.0, 20.0, 20.0), building
    )

    def set_invalid_demand(self, *args):
        self.energy_demand_unrestricted = float("nan")

    building.calc_energy_demand_unrestricted = MethodType(set_invalid_demand, building)

    with pytest.raises(ThermalCalculationError) as raised:
        building.calc_energy_demand(0.0, 0.0, 10.0, 20.0)

    assert raised.value.phase == "simulate_hours"