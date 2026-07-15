"""Window construction, sun-position and window-gain calculations."""

import math
from typing import List, NamedTuple, Tuple

from dibs_computing_core.iso_simulator.model.location import Location
from dibs_computing_core.iso_simulator.model.weather_data import WeatherData
from dibs_computing_core.iso_simulator.model.window import Window


class WindowGainsResult(NamedTuple):
    """Named result of the combined window solar gains and illuminance calculation."""

    solar_gains_total: float
    transmitted_illuminance_total: float


class WindowCalculator:
    """Build windows and calculate solar gains/illuminance for one building."""

    def __init__(self, building, datasource, weather_data: List[WeatherData]) -> None:
        self.building = building
        self.datasource = datasource
        self.weather_data = weather_data
        self.all_windows = self.build_windows_objects()
        self._sun_positions = self.precompute_sun_positions()

    def precompute_sun_positions(self) -> list[tuple[float, float]]:
        location = Location()
        latitude = self.datasource.epw_file.coordinates_station[0]
        longitude = self.datasource.epw_file.coordinates_station[1]
        return [
            location.calc_sun_position(latitude, longitude, hour_data.year, hour)
            for hour, hour_data in enumerate(self.weather_data)
        ]

    def _build_window(self, azimuth: float, area: float) -> Window:
        """Build a window with shared glazing values for one orientation."""
        return Window(
            azimuth,
            90,
            self.building.glass_solar_transmittance,
            self.building.glass_solar_shading_transmittance,
            self.building.glass_light_transmittance,
            area,
        )

    def build_south_window(self) -> Window:
        """Build the south-facing window."""
        return self._build_window(0, self.building.window_area_south)

    def build_east_window(self) -> Window:
        """Build the east-facing window."""
        return self._build_window(90, self.building.window_area_east)

    def build_west_window(self) -> Window:
        """Build the west-facing window."""
        return self._build_window(180, self.building.window_area_west)

    def build_north_window(self) -> Window:
        """Build the north-facing window."""
        return self._build_window(270, self.building.window_area_north)

    def build_windows_objects(self) -> List[Window]:
        """Build all windows in the historical south/east/west/north order."""
        return [
            self.build_south_window(),
            self.build_east_window(),
            self.build_west_window(),
            self.build_north_window(),
        ]

    def calc_altitude_and_azimuth(self, hour: int) -> Tuple[float, float]:
        """Return sun altitude and azimuth for the requested simulation hour."""
        if 0 <= hour < len(self._sun_positions):
            return self._sun_positions[hour]
        location = Location()
        return location.calc_sun_position(
            self.datasource.epw_file.coordinates_station[0],
            self.datasource.epw_file.coordinates_station[1],
            self.weather_data[hour].year,
            hour,
        )

    def calc_solar_gains_for_all_windows(
            self, sun_altitude: float, sun_azimuth: float, t_air: float, hour: int
    ) -> None:
        """Calculate solar gains for all windows."""
        hour_weather = self.weather_data[hour]
        dirnorrad = hour_weather.dirnorrad_Whm2
        difhorrad = hour_weather.difhorrad_Whm2

        for element in self.all_windows:
            element.calc_solar_gains(
                sun_altitude,
                sun_azimuth,
                dirnorrad,
                difhorrad,
                t_air,
                hour,
            )

    def calc_illuminance_for_all_windows(
            self, sun_altitude: float, sun_azimuth: float, hour: int
    ) -> None:
        """Calculate illuminance for all windows."""
        hour_weather = self.weather_data[hour]
        dirnorillum = hour_weather.dirnorillum_lux
        difhorillum = hour_weather.difhorillum_lux

        for element in self.all_windows:
            element.calc_illuminance(
                sun_altitude,
                sun_azimuth,
                dirnorillum,
                difhorillum,
            )

    def calc_window_gains_and_illuminance_for_all_windows(
            self,
            sun_altitude: float,
            sun_azimuth: float,
            t_air: float,
            hour: int,
            calculate_illuminance: bool = True,
    ) -> WindowGainsResult:
        """Calculate solar gains + illuminance for all windows in one pass."""
        hour_weather = self.weather_data[hour]
        dirnorrad = hour_weather.dirnorrad_Whm2
        difhorrad = hour_weather.difhorrad_Whm2
        sun_altitude_rad = math.radians(sun_altitude)
        sun_azimuth_rad = math.radians(sun_azimuth)
        sun_cos_altitude = math.cos(sun_altitude_rad)
        sun_sin_altitude = math.sin(sun_altitude_rad)

        solar_gains_sum = 0.0
        transmitted_illuminance_sum = 0.0

        if calculate_illuminance:
            dirnorillum = hour_weather.dirnorillum_lux
            difhorillum = hour_weather.difhorillum_lux
            for element in self.all_windows:
                direct_factor = element.calc_solar_gains_precomputed(
                    sun_cos_altitude,
                    sun_sin_altitude,
                    sun_azimuth_rad,
                    dirnorrad,
                    difhorrad,
                    t_air,
                    hour,
                )
                element.calc_illuminance_precomputed(
                    direct_factor,
                    difhorillum,
                    dirnorillum,
                )
                solar_gains_sum += element.solar_gains
                transmitted_illuminance_sum += element.transmitted_illuminance
        else:
            for element in self.all_windows:
                element.calc_solar_gains_precomputed(
                    sun_cos_altitude,
                    sun_sin_altitude,
                    sun_azimuth_rad,
                    dirnorrad,
                    difhorrad,
                    t_air,
                    hour,
                )
                element.transmitted_illuminance = 0.0
                solar_gains_sum += element.solar_gains

        return WindowGainsResult(
            solar_gains_total=solar_gains_sum,
            transmitted_illuminance_total=transmitted_illuminance_sum,
        )

    def calc_sum_illuminance_all_windows(self) -> float:
        """Return the sum of transmitted illuminance for all windows."""
        return sum(element.transmitted_illuminance for element in self.all_windows)

    def calc_sum_solar_gains_all_windows(self) -> float:
        """Return the sum of solar gains for all windows."""
        return sum(element.solar_gains for element in self.all_windows)
