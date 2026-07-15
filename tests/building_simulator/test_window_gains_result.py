from types import SimpleNamespace

from dibs_computing_core.iso_simulator.building_simulator.simulator import (
    BuildingSimulator,
    WindowGainsResult,
)
from dibs_computing_core.iso_simulator.building_simulator.window_calculator import (
    WindowCalculator,
)


class FakeWindow:
    def __init__(self, solar_gains: float, transmitted_illuminance: float) -> None:
        self.solar_gains = solar_gains
        self.transmitted_illuminance = transmitted_illuminance
        self.received_direct_factor = None

    def calc_solar_gains_precomputed(
        self,
        sun_cos_altitude,
        sun_sin_altitude,
        sun_azimuth_rad,
        dirnorrad,
        difhorrad,
        t_air,
        hour,
    ):
        self.received_direct_factor = self.solar_gains / 10
        return self.received_direct_factor

    def calc_illuminance_precomputed(self, direct_factor, difhorillum, dirnorillum):
        assert direct_factor == self.received_direct_factor


def _simulator_with_fake_windows() -> BuildingSimulator:
    simulator = BuildingSimulator.__new__(BuildingSimulator)
    simulator.datasource = SimpleNamespace(
        epw_file=SimpleNamespace(coordinates_station=(50.0, 8.0))
    )
    simulator.weather_data = [
        SimpleNamespace(
            year=2020,
            dirnorrad_Whm2=100,
            difhorrad_Whm2=20,
            dirnorillum_lux=300,
            difhorillum_lux=40,
        )
    ]
    simulator.building = SimpleNamespace(
        glass_solar_transmittance=0.55,
        glass_solar_shading_transmittance=0.35,
        glass_light_transmittance=0.72,
        window_area_south=10.0,
        window_area_east=20.0,
        window_area_west=30.0,
        window_area_north=40.0,
    )
    fake_windows = [
        FakeWindow(1.0, 10.0),
        FakeWindow(2.0, 20.0),
        FakeWindow(3.0, 30.0),
        FakeWindow(4.0, 40.0),
    ]
    simulator.window_calculator = WindowCalculator(
        simulator.building, simulator.datasource, simulator.weather_data
    )
    simulator.window_calculator.all_windows = fake_windows
    simulator.all_windows = fake_windows
    return simulator


def test_window_gains_result_exposes_named_totals():
    simulator = _simulator_with_fake_windows()

    result = simulator.calc_window_gains_and_illuminance_for_all_windows(
        sun_altitude=30,
        sun_azimuth=180,
        t_air=21,
        hour=0,
        calculate_illuminance=True,
    )

    assert isinstance(result, WindowGainsResult)
    assert result.solar_gains_total == 10.0
    assert result.transmitted_illuminance_total == 100.0


def test_window_gains_result_sets_zero_illuminance_when_disabled():
    simulator = _simulator_with_fake_windows()

    result = simulator.calc_window_gains_and_illuminance_for_all_windows(
        sun_altitude=30,
        sun_azimuth=180,
        t_air=21,
        hour=0,
        calculate_illuminance=False,
    )

    assert result.solar_gains_total == 10.0
    assert result.transmitted_illuminance_total == 0.0
    assert [window.transmitted_illuminance for window in simulator.all_windows] == [
        0.0,
        0.0,
        0.0,
        0.0,
    ]
