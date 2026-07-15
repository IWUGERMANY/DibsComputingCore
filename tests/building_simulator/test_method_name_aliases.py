from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator


def _simulator() -> BuildingSimulator:
    return BuildingSimulator.__new__(BuildingSimulator)


def test_sys_electricity_fossils_sum_uses_correct_method_name():
    simulator = _simulator()

    assert simulator.sys_electricity_fossils_sum(3, 4.5) == 7.5


def test_cooling_system_electricity_sum_uses_correct_method_name():
    simulator = _simulator()
    sum_object = SimpleNamespace(
        Cooling_Sys_Electricity_sum=200.0,
        Cooling_Sys_Fossils_sum=0.0,
    )

    result = simulator.check_cooling_system_electricity_sum(sum_object, 2.0, 300, 1.5)

    assert result == (100.0, 30.0, 150.0, 0)


def test_solve_building_lighting_uses_correct_method_name():
    simulator = _simulator()
    simulator.all_windows = [
        SimpleNamespace(transmitted_illuminance=10.0),
        SimpleNamespace(transmitted_illuminance=15.0),
    ]
    calls = []
    simulator.building = SimpleNamespace(
        solve_building_lighting=lambda illuminance, occupancy: calls.append(
            (illuminance, occupancy)
        )
    )

    simulator.solve_building_lighting(0.75)

    assert calls == [(25.0, 0.75)]
