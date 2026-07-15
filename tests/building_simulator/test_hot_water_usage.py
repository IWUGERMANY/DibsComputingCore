from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator


def _simulator_for_dhw(
    dhw_system: str,
    heating_supply_system: str = "GasBoilerCondensingFrom95",
) -> BuildingSimulator:
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.building = SimpleNamespace(
        dhw_system=dhw_system,
        heating_supply_system=heating_supply_system,
        energy_ref_area=100.0,
        heating_demand=200.0,
        heating_energy=300.0,
    )
    return simulator


def test_hot_water_usage_returns_zero_without_dhw_system():
    simulator = _simulator_for_dhw("NoDHW")

    result = simulator.calc_hot_water_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert result == (0, 0, 0, 0)


def test_decentral_electric_dhw_assigns_energy_to_electricity():
    simulator = _simulator_for_dhw("DecentralElectricDHW")

    demand, energy, electricity, fossils = simulator.calc_hot_water_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert demand == 500.0
    assert energy == 750.0
    assert electricity == 750.0
    assert fossils == 0


def test_central_dhw_with_non_heat_pump_assigns_energy_to_fossils():
    simulator = _simulator_for_dhw("CentralDHW")

    demand, energy, electricity, fossils = simulator.calc_hot_water_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
        central_heating_or_dhw=True,
        heat_pump_air_or_ground=False,
    )

    assert demand == 500.0
    assert energy == 750.0
    assert electricity == 0
    assert fossils == 750.0


def test_central_dhw_with_heat_pump_assigns_energy_to_electricity():
    simulator = _simulator_for_dhw("CentralDHW", "HeatPumpAirSource")

    demand, energy, electricity, fossils = simulator.calc_hot_water_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
        central_heating_or_dhw=True,
        heat_pump_air_or_ground=True,
    )

    assert demand == 500.0
    assert energy == 750.0
    assert electricity == 750.0
    assert fossils == 0


def test_hot_water_energy_uses_demand_when_heating_demand_is_zero():
    simulator = _simulator_for_dhw("DecentralFuelBasedDHW")
    simulator.building.heating_demand = 0.0

    demand, energy, electricity, fossils = simulator.calc_hot_water_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert demand == 500.0
    assert energy == 500.0
    assert electricity == 0
    assert fossils == 500.0
