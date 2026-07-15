from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator


def _simulator() -> BuildingSimulator:
    return BuildingSimulator.__new__(BuildingSimulator)


def _sum_object(**overrides):
    values = {
        "Heating_Sys_Electricity_sum": 0.0,
        "Heating_Sys_Fossils_sum": 0.0,
        "HotWater_Sys_Electricity_sum": 0.0,
        "HotWater_Sys_Fossils_sum": 0.0,
        "Cooling_Sys_Electricity_sum": 0.0,
        "Cooling_Sys_Fossils_sum": 0.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_heating_system_totals_use_electricity_when_available():
    result = _simulator().check_heating_sys_electricity_sum(
        _sum_object(Heating_Sys_Electricity_sum=200.0, Heating_Sys_Fossils_sum=900.0),
        f_hs_hi=2.0,
        f_ghg=300,
        f_pe=1.5,
    )

    assert result == (100.0, 30.0, 150.0, 0)


def test_heating_system_totals_use_fossils_when_electricity_is_zero():
    result = _simulator().check_heating_sys_electricity_sum(
        _sum_object(Heating_Sys_Electricity_sum=0.0, Heating_Sys_Fossils_sum=900.0),
        f_hs_hi=3.0,
        f_ghg=200,
        f_pe=1.1,
    )

    assert result == (0, 60.0, 330.0, 300.0)


def test_hotwater_system_totals_keep_historical_return_order():
    result = _simulator().check_hotwater_sys_electricity_sum(
        _sum_object(HotWater_Sys_Electricity_sum=200.0, HotWater_Sys_Fossils_sum=900.0),
        f_hs_hi=2.0,
        f_ghg=300,
        f_pe=1.5,
    )

    assert result == (100.0, 150.0, 30.0, 0)


def test_cooling_system_totals_use_fossils_when_electricity_is_zero():
    result = _simulator().check_cooling_system_electricity_sum(
        _sum_object(Cooling_Sys_Electricity_sum=0.0, Cooling_Sys_Fossils_sum=800.0),
        f_hs_hi=4.0,
        f_ghg=250,
        f_pe=1.2,
    )

    assert result == (0, 50.0, 240.0, 200.0)
