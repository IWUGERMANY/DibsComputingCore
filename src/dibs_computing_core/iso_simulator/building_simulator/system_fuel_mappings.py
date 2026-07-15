"""Heating, cooling and DHW system mappings for BuildingSimulator."""

from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    CoolingSystem,
    DhwSystem,
    EnergyCarrier,
    HeatingSystem,
)


FUEL_ELECTRICITY_GRID_MIX = EnergyCarrier.ELECTRICITY_GRID_MIX.value
FUEL_NATURAL_GAS = EnergyCarrier.NATURAL_GAS.value

DHW_NO_SYSTEM_TYPES = frozenset({
    DhwSystem.NO_DHW.value,
    DhwSystem.UNKNOWN_EMPTY.value,
})
DHW_CENTRAL_TYPES = frozenset({
    DhwSystem.CENTRAL_HEATING.value,
    DhwSystem.CENTRAL_DHW.value,
})
DHW_DECENTRAL_ELECTRIC = DhwSystem.DECENTRAL_ELECTRIC_DHW.value
DHW_DECENTRAL_FUEL_BASED = DhwSystem.DECENTRAL_FUEL_BASED_DHW.value

HEATING_BIOGAS_BOILER_TYPES = frozenset({
    HeatingSystem.BIOGAS_BOILER_CONDENSING_BEFORE_95.value,
    HeatingSystem.BIOGAS_BOILER_CONDENSING_FROM_95.value,
})
HEATING_BIOGAS_OIL_BOILER_TYPES = frozenset({
    HeatingSystem.BIOGAS_OIL_BOILER_LOW_TEMP_BEFORE_95.value,
    HeatingSystem.BIOGAS_OIL_BOILER_CONDENSING_FROM_95.value,
    HeatingSystem.BIOGAS_OIL_BOILER_CONDENSING_IMPROVED.value,
})
HEATING_OIL_BOILER_TYPES = frozenset({
    HeatingSystem.OIL_BOILER_STANDARD_BEFORE_86.value,
    HeatingSystem.OIL_BOILER_STANDARD_FROM_95.value,
    HeatingSystem.OIL_BOILER_LOW_TEMP_BEFORE_87.value,
    HeatingSystem.OIL_BOILER_LOW_TEMP_BEFORE_95.value,
    HeatingSystem.OIL_BOILER_LOW_TEMP_FROM_95.value,
    HeatingSystem.OIL_BOILER_CONDENSING_BEFORE_95.value,
    HeatingSystem.OIL_BOILER_CONDENSING_FROM_95.value,
    HeatingSystem.OIL_BOILER_CONDENSING_IMPROVED.value,
})
HEATING_LGAS_BOILER_TYPES = frozenset({
    HeatingSystem.LGAS_BOILER_LOW_TEMP_BEFORE_95.value,
    HeatingSystem.LGAS_BOILER_LOW_TEMP_FROM_95.value,
    HeatingSystem.LGAS_BOILER_CONDENSING_BEFORE_95.value,
    HeatingSystem.LGAS_BOILER_CONDENSING_FROM_95.value,
    HeatingSystem.LGAS_BOILER_CONDENSING_IMPROVED.value,
    HeatingSystem.LGAS_BOILER_LOW_TEMP_BEFORE_87.value,
})
HEATING_GAS_BOILER_TYPES = frozenset({
    HeatingSystem.GAS_BOILER_STANDARD_BEFORE_86.value,
    HeatingSystem.GAS_BOILER_STANDARD_BEFORE_95.value,
    HeatingSystem.GAS_BOILER_STANDARD_FROM_95.value,
    HeatingSystem.GAS_BOILER_LOW_TEMP_BEFORE_87.value,
    HeatingSystem.GAS_BOILER_LOW_TEMP_BEFORE_95.value,
    HeatingSystem.GAS_BOILER_LOW_TEMP_FROM_95.value,
    HeatingSystem.GAS_BOILER_LOW_TEMP_SPECIAL_FROM_78.value,
    HeatingSystem.GAS_BOILER_LOW_TEMP_SPECIAL_FROM_95.value,
    HeatingSystem.GAS_BOILER_CONDENSING_BEFORE_95.value,
    HeatingSystem.GAS_BOILER_CONDENSING_IMPROVED.value,
    HeatingSystem.GAS_BOILER_CONDENSING_FROM_95.value,
})
HEATING_HEAT_PUMP_TYPES = frozenset({
    HeatingSystem.HEAT_PUMP_AIR_SOURCE.value,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE.value,
})
HEATING_WOOD_TYPES = frozenset({
    HeatingSystem.WOOD_CHIP_SOLID_FUEL_BOILER.value,
    HeatingSystem.WOOD_PELLET_SOLID_FUEL_BOILER.value,
    HeatingSystem.WOOD_SOLID_FUEL_BOILER_CENTRAL.value,
})

HEATING_FUEL_TYPES = {
    **dict.fromkeys(HEATING_BIOGAS_BOILER_TYPES, EnergyCarrier.BIOGAS_GENERAL.value),
    **dict.fromkeys(
        HEATING_BIOGAS_OIL_BOILER_TYPES,
        EnergyCarrier.BIOGAS_BIO_OIL_MIX_GENERAL.value,
    ),
    **dict.fromkeys(HEATING_OIL_BOILER_TYPES, EnergyCarrier.LIGHT_FUEL_OIL.value),
    **dict.fromkeys(HEATING_LGAS_BOILER_TYPES, FUEL_NATURAL_GAS),
    **dict.fromkeys(HEATING_GAS_BOILER_TYPES, FUEL_NATURAL_GAS),
    **dict.fromkeys(HEATING_WOOD_TYPES, EnergyCarrier.WOOD.value),
    HeatingSystem.COAL_SOLID_FUEL_BOILER.value: EnergyCarrier.HARD_COAL.value,
    HeatingSystem.SOLID_FUEL_LIQUID_FUEL_FURNACE.value: EnergyCarrier.HARD_COAL.value,
    **dict.fromkeys(HEATING_HEAT_PUMP_TYPES, FUEL_ELECTRICITY_GRID_MIX),
    HeatingSystem.GAS_CHP.value: FUEL_NATURAL_GAS,
    HeatingSystem.DISTRICT_HEATING.value: EnergyCarrier.DISTRICT_HEATING_CHP_GAS_OR_LIQUID.value,
    HeatingSystem.ELECTRIC_HEATING.value: FUEL_ELECTRICITY_GRID_MIX,
    HeatingSystem.DIRECT_HEATER.value: EnergyCarrier.DISTRICT_HEATING_CHP_COAL.value,
    HeatingSystem.NO_HEATING.value: EnergyCarrier.NONE.value,
}

COOLING_AIR_TYPES = frozenset({
    CoolingSystem.AIR_COOLED_PISTON_SCROLL.value,
    CoolingSystem.AIR_COOLED_PISTON_SCROLL_MULTI.value,
    CoolingSystem.WATER_COOLED_PISTON_SCROLL.value,
    CoolingSystem.DIRECT_COOLER.value,
})
COOLING_FUEL_TYPES = {
    **dict.fromkeys(COOLING_AIR_TYPES, FUEL_ELECTRICITY_GRID_MIX),
    CoolingSystem.ABSORPTION_REFRIGERATION_SYSTEM.value: EnergyCarrier.WASTE_HEAT_CLOSE_TO_BUILDING.value,
    CoolingSystem.DISTRICT_COOLING.value: EnergyCarrier.DISTRICT_COOLING.value,
    CoolingSystem.GAS_ENGINE_PISTON_SCROLL.value: FUEL_NATURAL_GAS,
    CoolingSystem.NO_COOLING.value: EnergyCarrier.NONE.value,
}
