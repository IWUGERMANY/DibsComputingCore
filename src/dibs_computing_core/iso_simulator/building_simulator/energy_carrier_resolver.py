"""Energy carrier and factor resolution for building simulations."""

from typing import NamedTuple

from dibs_computing_core.iso_simulator.building_simulator.system_fuel_mappings import (
    COOLING_FUEL_TYPES,
    DHW_DECENTRAL_ELECTRIC,
    DHW_DECENTRAL_FUEL_BASED,
    FUEL_ELECTRICITY_GRID_MIX,
    FUEL_NATURAL_GAS,
    HEATING_FUEL_TYPES,
)
from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    system_key,
)
from dibs_computing_core.iso_simulator.exceptions import UnsupportedSystemError


class EnergyFactors(NamedTuple):
    """GHG, primary-energy and Hs/Hi factors for one energy carrier."""

    ghg: float | None
    primary_energy: float | None
    hs_hi: float | None
    fuel_type: str


class EnergyCarrierResolver:
    """Resolve system names to energy carriers and factor bundles."""

    def __init__(self, datasource, building=None) -> None:
        self.datasource = datasource
        self.building = building

    def choose_heating_fuel_type(self) -> str:
        """Choose the GHG fuel type for the configured heating system."""
        heating_supply_system = system_key(self.building.heating_supply_system)
        fuel_type = HEATING_FUEL_TYPES.get(heating_supply_system)
        if fuel_type is not None:
            return fuel_type

        raise UnsupportedSystemError(
            f"Unsupported heating supply system: {heating_supply_system}",
            phase="calculate_ghg",
            context={
                "building_id": self.building.scr_gebaeude_id,
                "heating_supply_system": heating_supply_system,
            },
        )

    def choose_cooling_energy_fuel_type(self) -> str:
        """Choose the GHG fuel type for the configured cooling system."""
        cooling_supply_system = system_key(self.building.cooling_supply_system)
        fuel_type = COOLING_FUEL_TYPES.get(cooling_supply_system)
        if fuel_type is not None:
            return fuel_type

        raise UnsupportedSystemError(
            f"Unsupported cooling supply system: {cooling_supply_system}",
            phase="calculate_ghg",
            context={
                "building_id": self.building.scr_gebaeude_id,
                "cooling_supply_system": cooling_supply_system,
            },
        )

    def get_energy_factors(self, fuel_type: str) -> EnergyFactors:
        """Return all configured emission and primary-energy factors for one fuel type."""
        fuel_type = system_key(fuel_type)
        for factor in self.datasource.epw_pe_factors:
            if factor.energy_carrier == fuel_type:
                return EnergyFactors(
                    ghg=factor.gwp_spezific_to_heating_value_GEG,
                    primary_energy=factor.primary_energy_factor_GEG,
                    hs_hi=factor.relation_calorific_to_heating_value_GEG,
                    fuel_type=fuel_type,
                )
        return EnergyFactors(
            ghg=None,
            primary_energy=None,
            hs_hi=None,
            fuel_type=fuel_type,
        )

    def get_ghg_factor(self, fuel_type: str):
        return self.get_energy_factors(fuel_type).ghg

    def get_primary_energy_factor(self, fuel_type: str):
        return self.get_energy_factors(fuel_type).primary_energy

    def get_hs_hi_factor(self, fuel_type: str):
        return self.get_energy_factors(fuel_type).hs_hi

    def choose_hot_water_fuel_type(self, heating_fuel_type: str) -> str:
        """Choose DHW fuel type, preserving central-DHW coupling to heating."""
        dhw_system = system_key(self.building.dhw_system)
        if dhw_system == DHW_DECENTRAL_ELECTRIC:
            return FUEL_ELECTRICITY_GRID_MIX
        if dhw_system == DHW_DECENTRAL_FUEL_BASED:
            return FUEL_NATURAL_GAS
        return heating_fuel_type
