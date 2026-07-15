from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.occupancy_and_gains_calculator import (
    OccupancyAndGainsCalculator,
)


def _calculator() -> OccupancyAndGainsCalculator:
    building = SimpleNamespace(
        max_occupancy=20.0,
        energy_ref_area=100.0,
        lighting_demand=15.0,
    )
    return OccupancyAndGainsCalculator(building)


def test_calc_occupancy_uses_people_share_and_max_occupancy():
    schedule = [SimpleNamespace(People=0.25, Appliances=0.4)]

    assert _calculator().calc_occupancy(schedule, 0) == 5.0


def test_calc_gains_from_occupancy_and_appliances_keeps_formula():
    schedule = [SimpleNamespace(People=0.25, Appliances=0.4)]

    result = _calculator().calc_gains_from_occupancy_and_appliances(
        schedule,
        occupancy=5.0,
        gain_per_person=80.0,
        appliance_gains=10.0,
        hour=0,
    )

    assert result == 815.0


def test_calc_appliance_gains_demand_uses_area_and_schedule():
    schedule = [SimpleNamespace(People=0.25, Appliances=0.4)]

    assert _calculator().calc_appliance_gains_demand(schedule, 10.0, 0) == 400.0


def test_negative_appliance_gains_are_converted_to_electric_demand():
    schedule = [SimpleNamespace(People=0.25, Appliances=0.4)]

    assert _calculator().get_appliance_gains_elt_demand(schedule, -10.0, 0) == 200.0
