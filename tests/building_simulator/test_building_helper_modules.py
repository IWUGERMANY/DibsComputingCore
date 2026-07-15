from types import SimpleNamespace

from dibs_computing_core.iso_simulator.emission_system import EmissionDirector
from dibs_computing_core.iso_simulator.model.building_energy import (
    _demand_flags,
    _is_within_available_power,
    calc_energy_demand,
    calc_energy_demand_unrestricted,
    solve_building_energy,
)
from dibs_computing_core.iso_simulator.model.building_heat_flow import calc_heat_flow
from dibs_computing_core.iso_simulator.model.building_lighting import solve_building_lighting
from dibs_computing_core.iso_simulator.model.building_ventilation import (
    _is_night_flushing_active,
    _is_usage_time,
    calc_h_ve_adj,
    check_night_flushing,
)


def test_demand_flags_keep_original_heating_priority():
    assert _demand_flags(19.9, 20.0, 26.0) == (True, False)
    assert _demand_flags(26.1, 20.0, 26.0) == (False, True)
    assert _demand_flags(22.0, 20.0, 26.0) == (False, False)
    assert _demand_flags(19.0, 20.0, 18.0) == (True, False)

def test_usage_time_supports_daytime_and_overnight_windows():
    assert _is_usage_time(daytime=10, usage_start=8, usage_end=18)
    assert not _is_usage_time(daytime=22, usage_start=8, usage_end=18)
    assert _is_usage_time(daytime=22, usage_start=20, usage_end=6)
    assert _is_usage_time(daytime=3, usage_start=20, usage_end=6)
    assert not _is_usage_time(daytime=12, usage_start=20, usage_end=6)


def _ventilation_building(**overrides):
    values = {
        "ach_inf": 0.1,
        "ach_vent": 0.5,
        "ach_win": 0.2,
        "b_ek": 0.8,
        "building_vol": 1000.0,
        "night_flushing_flow": 4.0,
        "night_flushing_on": False,
        "t_air": 22.5,
        "t_set_heating": 20,
    }
    values.update(overrides)
    building = SimpleNamespace(**values)
    building.check_night_flushing = lambda hour, t_out: check_night_flushing(
        building, hour, t_out
    )
    return building


def test_ventilation_uses_infiltration_when_no_ventilation_or_window_air_exchange():
    building = _ventilation_building(ach_vent=0, ach_win=0)

    result = calc_h_ve_adj(building, hour=12, t_out=10, usage_start=8, usage_end=18)

    assert result == 1200 * building.building_vol * (building.ach_inf / 3600)
    assert building.t_set_heating == 20


def test_ventilation_uses_usage_value_inside_usage_time():
    building = _ventilation_building(night_flushing_flow=0)

    result = calc_h_ve_adj(building, hour=12, t_out=10, usage_start=8, usage_end=18)

    expected = 1200 * (
        (building.b_ek * building.building_vol * (building.ach_vent / 3600))
        + (building.building_vol * (building.ach_win / 3600))
    )
    assert result == expected


def test_ventilation_night_flushing_sets_heating_setpoint_to_zero():
    building = _ventilation_building(t_air=24.0)

    result = calc_h_ve_adj(building, hour=2184, t_out=15, usage_start=8, usage_end=18)

    assert result == 1200 * building.building_vol * (building.night_flushing_flow / 3600)
    assert building.t_set_heating == 0


def test_lighting_switches_on_below_lux_threshold_with_occupancy():
    building = SimpleNamespace(
        lighting_utilisation_factor=1.0,
        lighting_maintenance_factor=1.0,
        net_room_area=100.0,
        lighting_control=300,
        lighting_load=10.0,
        lighting_demand=None,
    )

    solve_building_lighting(building, illuminance=1000.0, occupancy=0.5)

    assert building.lighting_demand == 500.0


def test_lighting_stays_off_without_occupancy():
    building = SimpleNamespace(
        lighting_utilisation_factor=1.0,
        lighting_maintenance_factor=1.0,
        net_room_area=100.0,
        lighting_control=300,
        lighting_load=10.0,
        lighting_demand=None,
    )

    solve_building_lighting(building, illuminance=1000.0, occupancy=0.0)

    assert building.lighting_demand == 0


class _FakeFlows:
    phi_ia_plus = 1.0
    phi_st_plus = 2.0
    phi_m_plus = 3.0
    heating_supply_temperature = 45
    cooling_supply_temperature = 12


class _FakeEmissionSystem:
    def __init__(self, energy_demand):
        self.energy_demand = energy_demand

    def heat_flows(self):
        return _FakeFlows()


def test_heat_flow_adds_emission_flows_and_sets_supply_temperatures():
    building = SimpleNamespace(
        mass_area=50.0,
        A_t=200.0,
        h_tr_w=20.0,
        _emission_director=EmissionDirector(),
        _heating_emission_cls=_FakeEmissionSystem,
        _cooling_emission_cls=_FakeEmissionSystem,
    )

    calc_heat_flow(
        building,
        t_out=5.0,
        internal_gains=100.0,
        solar_gains=200.0,
        energy_demand=500.0,
    )

    base_air = 0.5 * 100.0
    base_surface = (1 - (50.0 / 200.0) - (20.0 / (9.1 * 200.0))) * (50.0 + 200.0)
    base_mass = (50.0 / 200.0) * (50.0 + 200.0)
    assert building.phi_ia == base_air + 1.0
    assert building.phi_st == base_surface + 2.0
    assert building.phi_m == base_mass + 3.0
    assert building.heating_supply_temperature == 45
    assert building.cooling_supply_temperature == 12


def test_solve_building_energy_sets_zero_totals_without_demand():
    building = SimpleNamespace(
        has_heating_demand=True,
        has_cooling_demand=True,
    )
    building.has_demand = lambda internal_gains, solar_gains, t_out, t_m_prev: (
        setattr(building, "has_heating_demand", False),
        setattr(building, "has_cooling_demand", False),
    )

    solve_building_energy(
        building,
        internal_gains=0.0,
        solar_gains=0.0,
        t_out=10.0,
        t_m_prev=20.0,
    )

    assert building.energy_demand == 0
    assert building.heating_demand == 0
    assert building.cooling_demand == 0
    assert building.heating_sys_electricity == 0
    assert building.heating_sys_fossils == 0
    assert building.cooling_sys_electricity == 0
    assert building.cooling_sys_fossils == 0
    assert building.electricity_out == 0
    assert building.sys_total_energy == 0
    assert building.heating_energy == 0
    assert building.cooling_energy == 0


def test_unrestricted_energy_demand_uses_ten_watt_reference_case():
    building = SimpleNamespace()

    calc_energy_demand_unrestricted(
        building,
        energy_floorAx10=1000.0,
        t_air_set=21.0,
        t_air_0=19.0,
        t_air_10=23.0,
    )

    assert building.energy_demand_unrestricted == 500.0


def test_energy_demand_reuses_no_demand_temperature_from_has_demand():
    calls = []
    building = SimpleNamespace(
        has_heating_demand=True,
        has_cooling_demand=False,
        t_set_heating=21.0,
        t_set_cooling=26.0,
        _energy_floor_ax10=1000.0,
        max_cooling_energy=-10000.0,
        max_heating_energy=10000.0,
        _last_no_demand_temperature_context=(100.0, 200.0, 5.0, 20.0, 19.0),
    )

    def calc_temperatures(energy_demand, internal_gains, solar_gains, t_out, t_m_prev):
        calls.append(energy_demand)
        if energy_demand == 0:
            raise AssertionError("no-demand temperature should have been reused")
        if energy_demand == building._energy_floor_ax10:
            return 0.0, 23.0, 0.0
        return 0.0, 21.0, 0.0

    building.calc_temperatures_crank_nicolson = calc_temperatures
    building.calc_energy_demand_unrestricted = lambda energy_floor_ax10, t_air_set, t_air_0, t_air_10: calc_energy_demand_unrestricted(
        building, energy_floor_ax10, t_air_set, t_air_0, t_air_10
    )

    calc_energy_demand(
        building,
        internal_gains=100.0,
        solar_gains=200.0,
        t_out=5.0,
        t_m_prev=20.0,
    )

    assert calls == [1000.0, 500.0]
    assert building.energy_demand_unrestricted == 500.0
    assert building.energy_demand == 500.0


def test_night_flushing_active_condition_is_named_and_stable():
    building = _ventilation_building(t_air=24.0)

    assert _is_night_flushing_active(building, hour=2184, t_out=15) is True

    building.night_flushing_flow = 0
    assert _is_night_flushing_active(building, hour=2184, t_out=15) is False


def test_available_power_condition_accepts_values_inside_limits():
    building = SimpleNamespace(
        max_cooling_energy=-100.0,
        energy_demand_unrestricted=50.0,
        max_heating_energy=100.0,
    )

    assert _is_within_available_power(building) is True

    building.energy_demand_unrestricted = 150.0
    assert _is_within_available_power(building) is False


def test_night_flushing_inactive_does_not_require_t_air():
    building = SimpleNamespace(night_flushing_flow=0)

    assert _is_night_flushing_active(building, hour=2184, t_out=15) is False
