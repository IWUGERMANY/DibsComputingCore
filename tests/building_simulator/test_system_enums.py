from types import SimpleNamespace

from dibs_computing_core.iso_simulator.model.building import Building
from dibs_computing_core.iso_simulator.model.building_system_mappings import (
    BUILDING_EMISSION_SYSTEM_MAPPING,
    BUILDING_SUPPLY_SYSTEM_MAPPING,
    COOLING_SUPPLY_SYSTEM_MAPPING,
    HEATING_SUPPLY_SYSTEM_MAPPING,
)
from dibs_computing_core.iso_simulator.building_simulator.energy_carrier_resolver import (
    EnergyCarrierResolver,
)
from dibs_computing_core.iso_simulator.building_simulator.hot_water_calculator import (
    HotWaterCalculator,
)
from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    CoolingSystem,
    DhwSystem,
    EmissionSystem,
    EnergyCarrier,
    HeatingSystem,
    enum_value,
    system_key,
)


def test_system_key_documents_datasource_string_compatibility():
    assert system_key("NoHeating") == "NoHeating"
    assert system_key(HeatingSystem.NO_HEATING) == "NoHeating"
    assert enum_value(HeatingSystem.NO_HEATING) == system_key(HeatingSystem.NO_HEATING)


def test_energy_carrier_enum_is_string_compatible():
    assert EnergyCarrier.NATURAL_GAS == "Natural gas"
    assert str(EnergyCarrier.NATURAL_GAS) == "Natural gas"


def test_resolver_accepts_heating_and_cooling_enums():
    building = SimpleNamespace(
        scr_gebaeude_id=1,
        heating_supply_system=HeatingSystem.GAS_BOILER_CONDENSING_FROM_95,
        cooling_supply_system=CoolingSystem.DISTRICT_COOLING,
    )
    resolver = EnergyCarrierResolver(datasource=None, building=building)

    assert resolver.choose_heating_fuel_type() == EnergyCarrier.NATURAL_GAS.value
    assert resolver.choose_cooling_energy_fuel_type() == EnergyCarrier.DISTRICT_COOLING.value


def test_hot_water_calculator_accepts_dhw_enums():
    building = SimpleNamespace(
        dhw_system=DhwSystem.CENTRAL_DHW,
        heating_supply_system=HeatingSystem.HEAT_PUMP_AIR_SOURCE,
        energy_ref_area=100.0,
        heating_demand=200.0,
        heating_energy=300.0,
    )
    calculator = HotWaterCalculator(building)

    assert calculator.has_hot_water_system() is True
    assert calculator.has_central_heating_or_dhw() is True
    assert calculator.has_heat_pump_air_or_ground_source() is True


def test_building_system_mappings_accept_system_enums():
    building = Building(
        scr_gebaeude_id="enum-building",
        plz="64283",
        hk_geb="office",
        uk_geb="office",
        max_occupancy=1,
        wall_area_og=100.0,
        wall_area_ug=0.0,
        window_area_north=5.0,
        window_area_east=5.0,
        window_area_south=5.0,
        window_area_west=5.0,
        roof_area=100.0,
        net_room_area=100.0,
        energy_ref_area=100.0,
        base_area=100.0,
        gross_base_area=100.0,
        building_height=3.0,
        net_volume=300.0,
        gross_volume=300.0,
        envelope_area=320.0,
        lighting_load=10.0,
        lighting_control=300,
        lighting_utilisation_factor=0.5,
        lighting_maintenance_factor=0.8,
        aw_construction=1,
        shading_device=0,
        shading_solar_transmittance=0.5,
        glass_solar_transmittance=0.6,
        glass_solar_shading_transmittance=0.3,
        glass_light_transmittance=0.7,
        u_windows=1.0,
        u_walls=0.3,
        u_roof=0.2,
        u_base=0.4,
        temp_adj_base=0.5,
        temp_adj_walls_ug=0.5,
        ach_inf=0.1,
        ach_win=0.2,
        ach_vent=0.3,
        heat_recovery_efficiency=0,
        thermal_capacitance=165000,
        t_set_heating=20,
        t_start=20,
        t_set_cooling=26,
        night_flushing_flow=0,
        max_heating_energy_per_floor_area=100.0,
        max_cooling_energy_per_floor_area=100.0,
        heating_supply_system=HeatingSystem.NO_HEATING,
        cooling_supply_system=CoolingSystem.NO_COOLING,
        heating_emission_system=EmissionSystem.NO_HEATING,
        cooling_emission_system=EmissionSystem.NO_COOLING,
        dhw_system=DhwSystem.NO_DHW,
    )

    assert building._heating_supply_cls.__name__ == "NoHeater"
    assert building._cooling_supply_cls.__name__ == "NoCooler"
    assert building._heating_emission_cls.__name__ == "NoHeating"
    assert building._cooling_emission_cls.__name__ == "NoCooling"

def test_building_supply_mapping_is_composed_from_heating_and_cooling_groups():
    assert BUILDING_SUPPLY_SYSTEM_MAPPING == {
        **HEATING_SUPPLY_SYSTEM_MAPPING,
        **COOLING_SUPPLY_SYSTEM_MAPPING,
    }
    assert not set(HEATING_SUPPLY_SYSTEM_MAPPING).intersection(
        COOLING_SUPPLY_SYSTEM_MAPPING
    )


def test_building_mapping_contains_key_special_systems():
    assert (
        HEATING_SUPPLY_SYSTEM_MAPPING[HeatingSystem.NO_HEATING.value].__name__
        == "NoHeater"
    )
    assert (
        HEATING_SUPPLY_SYSTEM_MAPPING[HeatingSystem.DISTRICT_HEATING.value].__name__
        == "DistrictHeating"
    )
    assert (
        COOLING_SUPPLY_SYSTEM_MAPPING[CoolingSystem.NO_COOLING.value].__name__
        == "NoCooler"
    )
    assert (
        COOLING_SUPPLY_SYSTEM_MAPPING[CoolingSystem.DISTRICT_COOLING.value].__name__
        == "DistrictCooling"
    )
    assert (
        BUILDING_EMISSION_SYSTEM_MAPPING[EmissionSystem.NO_HEATING.value].__name__
        == "NoHeating"
    )
    assert (
        BUILDING_EMISSION_SYSTEM_MAPPING[EmissionSystem.NO_COOLING.value].__name__
        == "NoCooling"
    )
