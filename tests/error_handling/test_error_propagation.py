"""Tests for failure propagation introduced in D-EH4."""

from types import SimpleNamespace

import pytest

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.building_simulator.system_enums import HeatingSystem
from dibs_computing_core.iso_simulator.dibs.dibs_utils.dibs_auxiliary_functions import (
    extracted_method_to_simulate_one_building,
)
from dibs_computing_core.iso_simulator.exceptions import (
    BuildingNotHeatedError,
    UnsupportedSystemError,
)


def make_simulator(**building_values) -> BuildingSimulator:
    defaults = {
        "scr_gebaeude_id": 101,
        "energy_ref_area": 100.0,
        "heating_supply_system": "GasBoilerCondensingBefore95",
        "cooling_supply_system": "NoCooling",
    }
    defaults.update(building_values)
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.datasource = SimpleNamespace(building=SimpleNamespace(**defaults))
    simulator.building = simulator.datasource.building
    return simulator


@pytest.mark.parametrize(
    "building_values",
    [
        {"energy_ref_area": -8},
        {"heating_supply_system": "NoHeating"},
        {"heating_supply_system": HeatingSystem.NO_HEATING},
    ],
)
def test_unheated_building_error_is_propagated(building_values, capsys):
    simulator = make_simulator(**building_values)

    with pytest.raises(BuildingNotHeatedError) as raised:
        simulator.check_energy_area_and_heating()

    error = raised.value
    assert error.phase == "simulate_hours"
    assert error.context["building_id"] == 101
    assert capsys.readouterr().out == ""


def test_extracted_simulation_stops_before_hourly_work_for_unheated_building():
    simulator = make_simulator(heating_supply_system="NoHeating")

    with pytest.raises(BuildingNotHeatedError):
        extracted_method_to_simulate_one_building(simulator, 20.0)


def test_unknown_heating_system_error_is_propagated(capsys):
    simulator = make_simulator(heating_supply_system="UnknownHeatingSystem")

    with pytest.raises(UnsupportedSystemError) as raised:
        simulator.choose_the_fuel_type()

    assert raised.value.phase == "calculate_ghg"
    assert raised.value.context == {
        "building_id": 101,
        "heating_supply_system": "UnknownHeatingSystem",
    }
    assert capsys.readouterr().out == ""


def test_district_cooling_maps_to_district_cooling_fuel_type(capsys):
    simulator = make_simulator(cooling_supply_system="DistrictCooling")

    assert simulator.choose_cooling_energy_fuel_type() == "District cooling"
    assert capsys.readouterr().out == ""


def test_unknown_cooling_system_error_is_propagated(capsys):
    simulator = make_simulator(cooling_supply_system="UnknownCoolingSystem")

    with pytest.raises(UnsupportedSystemError) as raised:
        simulator.choose_cooling_energy_fuel_type()

    assert raised.value.phase == "calculate_ghg"
    assert raised.value.context == {
        "building_id": 101,
        "cooling_supply_system": "UnknownCoolingSystem",
    }
    assert capsys.readouterr().out == ""


