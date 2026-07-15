"""Domestic hot-water calculations for DIBS building simulations."""

from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    HeatingSystem,
    system_key,
)
from dibs_computing_core.iso_simulator.building_simulator.system_fuel_mappings import (
    DHW_CENTRAL_TYPES,
    DHW_DECENTRAL_ELECTRIC,
    DHW_NO_SYSTEM_TYPES,
)

HEAT_PUMP_OR_ELECTRIC_HEATING_TYPES = frozenset({
    HeatingSystem.HEAT_PUMP_AIR_SOURCE.value,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE.value,
    HeatingSystem.ELECTRIC_HEATING.value,
})


class HotWaterCalculator:
    """Calculate hourly DHW demand, energy and system energy split."""

    def __init__(self, building) -> None:
        self.building = building

    def has_hot_water_system(self) -> bool:
        """Return whether the building has a usable DHW system."""
        return system_key(self.building.dhw_system) not in DHW_NO_SYSTEM_TYPES

    def has_central_heating_or_dhw(self) -> bool:
        """Return whether DHW is coupled to a central heating/DHW system."""
        return system_key(self.building.dhw_system) in DHW_CENTRAL_TYPES

    def has_heat_pump_air_or_ground_source(self) -> bool:
        """Return whether the heating system should assign central DHW to electricity."""
        return system_key(self.building.heating_supply_system) in HEAT_PUMP_OR_ELECTRIC_HEATING_TYPES

    def calculate_demand(
            self, people_share: float, tek_dhw_per_occupancy_full_usage_hour: float
    ) -> float:
        """Calculate domestic hot water demand for one simulation hour."""
        return (
                people_share
                * tek_dhw_per_occupancy_full_usage_hour
                * 1000
                * self.building.energy_ref_area
        )

    def calculate_energy(self, hot_water_demand: float) -> float:
        """Calculate DHW energy using the current heating efficiency when available."""
        if self.building.heating_demand > 0:
            return hot_water_demand * (
                    self.building.heating_energy / self.building.heating_demand
            )
        return hot_water_demand

    def uses_electric_energy(
            self, central_heating_or_dhw: bool, heat_pump_air_or_ground: bool
    ) -> bool:
        """Return whether DHW energy is assigned to electricity instead of fossils."""
        return system_key(self.building.dhw_system) == DHW_DECENTRAL_ELECTRIC or (
                central_heating_or_dhw and heat_pump_air_or_ground
        )

    def split_energy_by_system(
            self,
            hot_water_energy: float,
            central_heating_or_dhw: bool,
            heat_pump_air_or_ground: bool,
    ) -> tuple[float, float]:
        """Split DHW energy into electricity and fossil system energy."""
        if self.uses_electric_energy(central_heating_or_dhw, heat_pump_air_or_ground):
            return hot_water_energy, 0
        return 0, hot_water_energy

    def calculate_usage(
            self,
            occupancy_schedule,
            tek_dhw_per_occupancy_full_usage_hour: float,
            hour: int,
            people_share: float | None = None,
            has_dhw: bool | None = None,
            central_heating_or_dhw: bool | None = None,
            heat_pump_air_or_ground: bool | None = None,
    ) -> tuple[float, float, float, float]:
        """Calculate demand, energy, electricity and fossil DHW values for one hour."""
        if has_dhw is None:
            has_dhw = self.has_hot_water_system()
        if not has_dhw:
            return 0, 0, 0, 0

        if people_share is None:
            people_share = occupancy_schedule[hour].People

        hot_water_demand = self.calculate_demand(
            people_share, tek_dhw_per_occupancy_full_usage_hour
        )
        hot_water_energy = self.calculate_energy(hot_water_demand)

        if central_heating_or_dhw is None:
            central_heating_or_dhw = self.has_central_heating_or_dhw()
        if heat_pump_air_or_ground is None:
            heat_pump_air_or_ground = self.has_heat_pump_air_or_ground_source()

        hot_water_sys_electricity, hot_water_sys_fossils = self.split_energy_by_system(
            hot_water_energy, central_heating_or_dhw, heat_pump_air_or_ground
        )

        return (
            hot_water_demand,
            hot_water_energy,
            hot_water_sys_electricity,
            hot_water_sys_fossils,
        )
