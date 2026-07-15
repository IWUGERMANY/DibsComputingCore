from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.hot_water_calculator import (
    HotWaterCalculator,
)


def _calculator(
    dhw_system: str,
    heating_supply_system: str = "GasBoilerCondensingFrom95",
) -> HotWaterCalculator:
    building = SimpleNamespace(
        dhw_system=dhw_system,
        heating_supply_system=heating_supply_system,
        energy_ref_area=100.0,
        heating_demand=200.0,
        heating_energy=300.0,
    )
    return HotWaterCalculator(building)


def test_calculate_usage_without_dhw_returns_zero_values():
    result = _calculator("NoDHW").calculate_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert result == (0, 0, 0, 0)


def test_calculate_usage_for_decentral_electric_dhw():
    demand, energy, electricity, fossils = _calculator("DecentralElectricDHW").calculate_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert demand == 500.0
    assert energy == 750.0
    assert electricity == 750.0
    assert fossils == 0


def test_central_heat_pump_dhw_uses_electricity():
    demand, energy, electricity, fossils = _calculator(
        "CentralDHW", "HeatPumpAirSource"
    ).calculate_usage(
        occupancy_schedule=[SimpleNamespace(People=0.5)],
        tek_dhw_per_occupancy_full_usage_hour=0.01,
        hour=0,
    )

    assert demand == 500.0
    assert energy == 750.0
    assert electricity == 750.0
    assert fossils == 0
