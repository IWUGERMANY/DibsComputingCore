from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.energy_carrier_resolver import (
    EnergyCarrierResolver,
)
from dibs_computing_core.iso_simulator.building_simulator.system_energy_calculator import (
    SystemEnergyCalculator,
    SystemEnergyTotals,
)


def _datasource_with_factors():
    return SimpleNamespace(
        epw_pe_factors=[
            SimpleNamespace(
                energy_carrier="Natural gas",
                gwp_spezific_to_heating_value_GEG=240,
                primary_energy_factor_GEG=1.1,
                relation_calorific_to_heating_value_GEG=1.11,
            )
        ]
    )


def test_energy_carrier_resolver_resolves_heating_and_factors():
    building = SimpleNamespace(
        scr_gebaeude_id="B1",
        heating_supply_system="GasBoilerCondensingFrom95",
    )
    resolver = EnergyCarrierResolver(_datasource_with_factors(), building)

    fuel_type = resolver.choose_heating_fuel_type()
    factors = resolver.get_energy_factors(fuel_type)

    assert fuel_type == "Natural gas"
    assert factors.ghg == 240
    assert factors.primary_energy == 1.1
    assert factors.hs_hi == 1.11


def test_system_energy_calculator_calculates_named_totals():
    totals = SystemEnergyCalculator().calculate(
        electricity_sum=200.0,
        fossils_sum=900.0,
        f_hs_hi=2.0,
        f_ghg=300,
        f_pe=1.5,
    )

    assert isinstance(totals, SystemEnergyTotals)
    assert totals.electricity_hi == 100.0
    assert totals.carbon == 30.0
    assert totals.primary_energy == 150.0
    assert totals.fossils_hi == 0
