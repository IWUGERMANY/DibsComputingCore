from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import (
    BuildingSimulator,
    EnergyFactors,
)


def _simulator_with_factors() -> BuildingSimulator:
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.datasource = SimpleNamespace(
        epw_pe_factors=[
            SimpleNamespace(
                energy_carrier="Natural gas",
                gwp_spezific_to_heating_value_GEG=240,
                primary_energy_factor_GEG=1.1,
                relation_calorific_to_heating_value_GEG=1.11,
            ),
            SimpleNamespace(
                energy_carrier="Electricity grid mix",
                gwp_spezific_to_heating_value_GEG=560,
                primary_energy_factor_GEG=1.8,
                relation_calorific_to_heating_value_GEG=1.0,
            ),
        ]
    )
    return simulator


def test_get_energy_factors_returns_named_factor_bundle():
    factors = _simulator_with_factors().get_energy_factors("Natural gas")

    assert isinstance(factors, EnergyFactors)
    assert factors.ghg == 240
    assert factors.primary_energy == 1.1
    assert factors.hs_hi == 1.11
    assert factors.fuel_type == "Natural gas"


def test_get_ghg_pe_conversion_factors_stays_unpack_compatible():
    f_ghg, f_pe, f_hs_hi, fuel_type = _simulator_with_factors().get_ghg_pe_conversion_factors(
        "Electricity grid mix"
    )

    assert f_ghg == 560
    assert f_pe == 1.8
    assert f_hs_hi == 1.0
    assert fuel_type == "Electricity grid mix"


def test_factor_compatibility_methods_read_from_same_bundle():
    simulator = _simulator_with_factors()

    assert simulator.get_ghg_factor_heating("Natural gas") == 240
    assert simulator.get_pe_factor_heating("Natural gas") == 1.1
    assert simulator.get_conversion_factor_heating("Natural gas") == 1.11


def test_unknown_energy_carrier_returns_none_factors_with_fuel_type():
    factors = _simulator_with_factors().get_energy_factors("Unknown")

    assert factors == EnergyFactors(
        ghg=None,
        primary_energy=None,
        hs_hi=None,
        fuel_type="Unknown",
    )
