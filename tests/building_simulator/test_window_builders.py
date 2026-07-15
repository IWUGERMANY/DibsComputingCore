"""Tests for BuildingSimulator window construction."""

import math
from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator


def make_simulator() -> BuildingSimulator:
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.datasource = SimpleNamespace(
        epw_file=SimpleNamespace(coordinates_station=(50.0, 8.0))
    )
    simulator.weather_data = []
    simulator.building = SimpleNamespace(
        glass_solar_transmittance=0.55,
        glass_solar_shading_transmittance=0.35,
        glass_light_transmittance=0.72,
        window_area_south=10.0,
        window_area_east=20.0,
        window_area_west=30.0,
        window_area_north=40.0,
    )
    return simulator


def assert_window(window, azimuth, area):
    assert math.isclose(window.azimuth_tilt_rad, math.radians(azimuth))
    assert math.isclose(window.alititude_tilt_rad, math.radians(90))
    assert window.glass_solar_transmittance == 0.55
    assert window.glass_solar_shading_transmittance == 0.35
    assert window.glass_light_transmittance == 0.72
    assert window.area == area


def test_window_builders_keep_orientation_order_and_shared_glazing_values():
    simulator = make_simulator()

    windows = simulator.build_windows_objects()

    assert len(windows) == 4
    assert_window(windows[0], 0, 10.0)
    assert_window(windows[1], 90, 20.0)
    assert_window(windows[2], 180, 30.0)
    assert_window(windows[3], 270, 40.0)