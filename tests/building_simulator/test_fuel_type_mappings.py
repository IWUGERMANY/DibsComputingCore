"""Tests for BuildingSimulator heating and cooling fuel mappings."""

from types import SimpleNamespace

import pytest

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.building_simulator.system_fuel_mappings import (
    COOLING_FUEL_TYPES,
    HEATING_FUEL_TYPES,
)
from dibs_computing_core.iso_simulator.exceptions import UnsupportedSystemError


def make_simulator(
    heating_supply_system="GasBoilerCondensingBefore95",
    cooling_supply_system="NoCooling",
) -> BuildingSimulator:
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.building = SimpleNamespace(
        scr_gebaeude_id=101,
        heating_supply_system=heating_supply_system,
        cooling_supply_system=cooling_supply_system,
    )
    return simulator


@pytest.mark.parametrize(
    ("heating_supply_system", "expected_fuel_type"),
    sorted(HEATING_FUEL_TYPES.items()),
)
def test_heating_supply_system_maps_to_expected_fuel_type(
    heating_supply_system,
    expected_fuel_type,
):
    simulator = make_simulator(heating_supply_system=heating_supply_system)

    assert simulator.choose_the_fuel_type() == expected_fuel_type


@pytest.mark.parametrize(
    ("cooling_supply_system", "expected_fuel_type"),
    sorted(COOLING_FUEL_TYPES.items()),
)
def test_cooling_supply_system_maps_to_expected_fuel_type(
    cooling_supply_system,
    expected_fuel_type,
):
    simulator = make_simulator(cooling_supply_system=cooling_supply_system)

    assert simulator.choose_cooling_energy_fuel_type() == expected_fuel_type


def test_unknown_heating_supply_system_raises_contextual_error():
    simulator = make_simulator(heating_supply_system="UnknownHeatingSystem")

    with pytest.raises(UnsupportedSystemError) as raised:
        simulator.choose_the_fuel_type()

    assert raised.value.phase == "calculate_ghg"
    assert raised.value.context == {
        "building_id": 101,
        "heating_supply_system": "UnknownHeatingSystem",
    }


def test_unknown_cooling_supply_system_raises_contextual_error():
    simulator = make_simulator(cooling_supply_system="UnknownCoolingSystem")

    with pytest.raises(UnsupportedSystemError) as raised:
        simulator.choose_cooling_energy_fuel_type()

    assert raised.value.phase == "calculate_ghg"
    assert raised.value.context == {
        "building_id": 101,
        "cooling_supply_system": "UnknownCoolingSystem",
    }