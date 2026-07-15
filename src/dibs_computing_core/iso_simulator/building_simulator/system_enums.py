"""Typed system and energy-carrier names used at DIBS mapping boundaries."""

from enum import Enum


class StringEnum(str, Enum):
    """String-compatible enum for DataSourceCSV/DataSourceDjango inputs."""

    def __str__(self) -> str:
        return self.value


class EnergyCarrier(StringEnum):
    BIOGAS_GENERAL = "Biogas (general)"
    BIOGAS_BIO_OIL_MIX_GENERAL = "Biogas Bio-oil Mix (general)"
    DISTRICT_COOLING = "District cooling"
    DISTRICT_HEATING_CHP_COAL = "District heating (Combined Heat and Power) Coal"
    DISTRICT_HEATING_CHP_GAS_OR_LIQUID = (
        "District heating (Combined Heat and Power) Gas or Liquid fuels"
    )
    ELECTRICITY_GRID_MIX = "Electricity grid mix"
    HARD_COAL = "Hard coal"
    LIGHT_FUEL_OIL = "Light fuel oil"
    NATURAL_GAS = "Natural gas"
    NONE = "None"
    WASTE_HEAT_CLOSE_TO_BUILDING = "Waste Heat generated close to building"
    WOOD = "Wood"


class DhwSystem(StringEnum):
    """Domestic hot-water system identifiers accepted by DIBS."""

    CENTRAL_DHW = "CentralDHW"
    CENTRAL_HEATING = "CentralHeating"
    DECENTRAL_ELECTRIC_DHW = "DecentralElectricDHW"
    DECENTRAL_FUEL_BASED_DHW = "DecentralFuelBasedDHW"
    NO_DHW = "NoDHW"
    UNKNOWN_EMPTY = " -"


class EmissionSystem(StringEnum):
    """Emission-system identifiers used for heat-flow distribution."""

    AIR_CONDITIONING = "AirConditioning"
    NO_COOLING = "NoCooling"
    NO_HEATING = "NoHeating"
    SURFACE_HEATING_COOLING = "SurfaceHeatingCooling"
    THERMALLY_ACTIVATED = "ThermallyActivated"


class CoolingSystem(StringEnum):
    """Cooling supply-system identifiers accepted by DIBS."""

    ABSORPTION_REFRIGERATION_SYSTEM = "AbsorptionRefrigerationSystem"
    AIR_COOLED_PISTON_SCROLL = "AirCooledPistonScroll"
    AIR_COOLED_PISTON_SCROLL_MULTI = "AirCooledPistonScrollMulti"
    DIRECT_COOLER = "DirectCooler"
    DISTRICT_COOLING = "DistrictCooling"
    GAS_ENGINE_PISTON_SCROLL = "GasEnginePistonScroll"
    NO_COOLING = "NoCooling"
    WATER_COOLED_PISTON_SCROLL = "WaterCooledPistonScroll"


class HeatingSystem(StringEnum):
    """Heating supply-system identifiers accepted by DIBS."""

    BIOGAS_BOILER_CONDENSING_BEFORE_95 = "BiogasBoilerCondensingBefore95"
    BIOGAS_BOILER_CONDENSING_FROM_95 = "BiogasBoilerCondensingFrom95"
    BIOGAS_OIL_BOILER_CONDENSING_FROM_95 = "BiogasOilBoilerCondensingFrom95"
    BIOGAS_OIL_BOILER_CONDENSING_IMPROVED = "BiogasOilBoilerCondensingImproved"
    BIOGAS_OIL_BOILER_LOW_TEMP_BEFORE_95 = "BiogasOilBoilerLowTempBefore95"
    COAL_SOLID_FUEL_BOILER = "CoalSolidFuelBoiler"
    DIRECT_HEATER = "DirectHeater"
    DISTRICT_HEATING = "DistrictHeating"
    ELECTRIC_HEATING = "ElectricHeating"
    GAS_BOILER_CONDENSING_BEFORE_95 = "GasBoilerCondensingBefore95"
    GAS_BOILER_CONDENSING_FROM_95 = "GasBoilerCondensingFrom95"
    GAS_BOILER_CONDENSING_IMPROVED = "GasBoilerCondensingImproved"
    GAS_BOILER_LOW_TEMP_BEFORE_87 = "GasBoilerLowTempBefore87"
    GAS_BOILER_LOW_TEMP_BEFORE_95 = "GasBoilerLowTempBefore95"
    GAS_BOILER_LOW_TEMP_FROM_95 = "GasBoilerLowTempFrom95"
    GAS_BOILER_LOW_TEMP_SPECIAL_FROM_78 = "GasBoilerLowTempSpecialFrom78"
    GAS_BOILER_LOW_TEMP_SPECIAL_FROM_95 = "GasBoilerLowTempSpecialFrom95"
    GAS_BOILER_STANDARD_BEFORE_86 = "GasBoilerStandardBefore86"
    GAS_BOILER_STANDARD_BEFORE_95 = "GasBoilerStandardBefore95"
    GAS_BOILER_STANDARD_FROM_95 = "GasBoilerStandardFrom95"
    GAS_CHP = "GasCHP"
    HEAT_PUMP_AIR_SOURCE = "HeatPumpAirSource"
    HEAT_PUMP_GROUND_SOURCE = "HeatPumpGroundSource"
    LGAS_BOILER_CONDENSING_BEFORE_95 = "LGasBoilerCondensingBefore95"
    LGAS_BOILER_CONDENSING_FROM_95 = "LGasBoilerCondensingFrom95"
    LGAS_BOILER_CONDENSING_IMPROVED = "LGasBoilerCondensingImproved"
    LGAS_BOILER_LOW_TEMP_BEFORE_87 = "LGasBoilerLowTempBefore87"
    LGAS_BOILER_LOW_TEMP_BEFORE_95 = "LGasBoilerLowTempBefore95"
    LGAS_BOILER_LOW_TEMP_FROM_95 = "LGasBoilerLowTempFrom95"
    NO_HEATING = "NoHeating"
    OIL_BOILER_CONDENSING_BEFORE_95 = "OilBoilerCondensingBefore95"
    OIL_BOILER_CONDENSING_FROM_95 = "OilBoilerCondensingFrom95"
    OIL_BOILER_CONDENSING_IMPROVED = "OilBoilerCondensingImproved"
    OIL_BOILER_LOW_TEMP_BEFORE_87 = "OilBoilerLowTempBefore87"
    OIL_BOILER_LOW_TEMP_BEFORE_95 = "OilBoilerLowTempBefore95"
    OIL_BOILER_LOW_TEMP_FROM_95 = "OilBoilerLowTempFrom95"
    OIL_BOILER_STANDARD_BEFORE_86 = "OilBoilerStandardBefore86"
    OIL_BOILER_STANDARD_FROM_95 = "OilBoilerStandardFrom95"
    SOLID_FUEL_LIQUID_FUEL_FURNACE = "SolidFuelLiquidFuelFurnace"
    WOOD_CHIP_SOLID_FUEL_BOILER = "WoodChipSolidFuelBoiler"
    WOOD_PELLET_SOLID_FUEL_BOILER = "WoodPelletSolidFuelBoiler"
    WOOD_SOLID_FUEL_BOILER_CENTRAL = "WoodSolidFuelBoilerCentral"


def system_key(value) -> str:
    """Normalize DataSource strings and internal enums to mapping keys.

    DataSourceCSV and DataSourceDjango still pass plain strings. Internal code may
    pass ``StringEnum`` values. Mapping boundaries should call this helper so both
    representations resolve to the same string key.
    """
    return value.value if isinstance(value, StringEnum) else value


def enum_value(value) -> str:
    """Backward-compatible alias for ``system_key``."""
    return system_key(value)