"""
this class implements the business logic to simulate a given building
"""
from dibs_computing_core.iso_simulator.model.calculations_sum import CalculationOfSum
from dibs_computing_core.iso_simulator.model.schedule_name import ScheduleName
from dibs_computing_core.iso_simulator.model.weather_data import WeatherData
from dibs_computing_core.iso_simulator.data_source.datasource import DataSource
from dibs_computing_core.iso_simulator.building_simulator.energy_carrier_resolver import (
    EnergyCarrierResolver,
    EnergyFactors,
)
from dibs_computing_core.iso_simulator.building_simulator.hot_water_calculator import (
    HotWaterCalculator,
)
from dibs_computing_core.iso_simulator.building_simulator.occupancy_and_gains_calculator import (
    OccupancyAndGainsCalculator,
)
from dibs_computing_core.iso_simulator.building_simulator.system_energy_calculator import (
    SystemEnergyCalculator,
    SystemEnergyTotals,
)
from dibs_computing_core.iso_simulator.building_simulator.window_calculator import (
    WindowCalculator,
    WindowGainsResult,
)
from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    HeatingSystem,
    system_key,
)
from dibs_computing_core.iso_simulator.exceptions.building_not_heated_exception import (
    BuildingNotHeatedError,
)

from typing import List, Tuple

__author__ = "Wail Samjouni"
__copyright__ = "Copyright 2023, Institut Wohnen und Umwelt"
__license__ = "MIT"


class BuildingSimulator:
    def __init__(
            self,
            datasource: DataSource
    ):
        """
        This constructor to initialize an instance of the BuildingSimulator class
        Args:
            datasource: object contains implemented methods of DataSource interface
        """
        self.datasource = datasource
        self.building = datasource.building
        self.energy_carrier_resolver = EnergyCarrierResolver(datasource, self.building)
        self.hot_water_calculator = HotWaterCalculator(self.building)
        self.occupancy_and_gains_calculator = OccupancyAndGainsCalculator(
            self.building
        )
        self.system_energy_calculator = SystemEnergyCalculator()
        self.weather_data = self.get_weather_data()
        self.window_calculator = WindowCalculator(
            self.building, self.datasource, self.weather_data
        )
        self.all_windows = self.window_calculator.all_windows

    def check_energy_area_and_heating(self) -> None:
        """Reject buildings for which no heating demand can be calculated."""
        building = self.building
        if (
            building.energy_ref_area == -8
            or system_key(building.heating_supply_system) == HeatingSystem.NO_HEATING.value
        ):
            raise BuildingNotHeatedError(
                f"Building {building.scr_gebaeude_id} not heated",
                phase="simulate_hours",
                context={
                    "building_id": building.scr_gebaeude_id,
                    "energy_ref_area": building.energy_ref_area,
                    "heating_supply_system": building.heating_supply_system,
                },
            )

    def _get_window_calculator(self) -> WindowCalculator:
        calculator = getattr(self, "window_calculator", None)
        if calculator is None:
            calculator = WindowCalculator(
                getattr(self, "building", None),
                self.datasource,
                self.weather_data,
            )
            self.window_calculator = calculator
            self.all_windows = calculator.all_windows
        return calculator

    def _build_window(self, azimuth: float, area: float):
        """Build a window with shared glazing values for one orientation."""
        return self._get_window_calculator()._build_window(azimuth, area)

    def build_south_window(self):
        """Build the south-facing window."""
        return self._get_window_calculator().build_south_window()

    def build_east_window(self):
        """Build the east-facing window."""
        return self._get_window_calculator().build_east_window()

    def build_west_window(self):
        """Build the west-facing window."""
        return self._get_window_calculator().build_west_window()

    def build_north_window(self):
        """Build the north-facing window."""
        return self._get_window_calculator().build_north_window()

    def build_windows_objects(self):
        """Build all windows in the historical south/east/west/north order."""
        return self._get_window_calculator().build_windows_objects()

    def get_usage_start_and_end(self) -> Tuple[int, int]:
        """
        Find building's usage time DIN 18599-10 or SIA2024
        Returns:
            usage_start, usage_end
        Return type
            Tuple[int, int]
        """
        usage_start, usage_end = self.datasource.get_usage_time()
        return usage_start, usage_end

    def get_schedule(self) -> Tuple[List[ScheduleName], str, float]:
        """Return the occupancy schedule provided by the data source.

        Raises:
            HkOrUkNotFoundError: If the HK/UK usage type cannot be resolved.
        """
        return self.datasource.get_schedule()

    def get_tek(self) -> Tuple[float, str]:
        """Return the TEK value and name provided by the data source.

        Raises:
            HkOrUkNotFoundError: If the HK/UK usage type cannot be resolved.
        """
        return self.datasource.get_tek()

    def get_weather_data(self) -> List[WeatherData]:
        """
        This method retrieves the right weather data according to the given weather_period and file_name

        Returns:
            weather_data_objects
        Return type
            List[WeatherData]
        """
        return self.datasource.choose_and_get_the_right_weather_data_from_path()

    def extract_outdoor_temperature(self, hour: int) -> float:
        """
        Extract the outdoor temperature in building_location for that hour from weather_data
        Args:
            hour: hour to simulate

        Returns:
            outdoor_temperature
        Return type
            float
        """
        return self.weather_data[hour].drybulb_C

    def extract_year(self, hour: int) -> int:
        """
        Extract the year based on a given hour
        Args:
            hour: hour to simulate

        Returns:
            year
        Return type
            int
        """
        return self.weather_data[hour].year

    def calc_altitude_and_azimuth(self, hour: int) -> Tuple[float, float]:
        """
        Call calc_sun_position(). Depending on latitude, longitude, year and hour - Independent from epw weather_data
        Args:
            hour: hour to simulate

        Returns:
            altitude, azimuth
        Return type
            Tuple[float, float]
        """
        return self._get_window_calculator().calc_altitude_and_azimuth(hour)

    def calc_building_h_ve_adj(
            self, hour: int, t_out: float, usage_start: int, usage_end: int
    ) -> float:
        """
        Calculate H_ve_adj, See building_physics for details
        Args:
            hour: hour to simulate
            t_out: Outdoor air temperature [C]
            usage_start: Beginning of usage time according to SIA2024
            usage_end: Ending of usage time according to SIA2024

        Returns:
            h_ve_adj
        Return type
            float
        """
        return self.building.calc_h_ve_adj(hour, t_out, usage_start, usage_end)

    def set_t_air_based_on_hour(self, hour: int) -> float:
        """
         Define t_air for calc_solar_gains(). Starting condition (hour==0) necessary for first time step
        Args:
            hour: hour to simulate

        Returns:
            t_air
        Return type
            float

        """
        t_air = (
            self.building.t_set_heating
            if hour == 0
            else self.building.t_air
        )
        return round(t_air, 2)

    def calc_solar_gains_for_all_windows(
            self, sun_altitude: float, sun_azimuth: float, t_air: float, hour: int
    ) -> None:
        """
        Calculates the solar gains in the building zone through the set window
        Args:
            sun_altitude: Altitude Angle of the Sun in Degrees
            sun_azimuth: Azimuth angle of the sun in degrees
            t_air:
            hour: hour to simulate

        Return type:
            None

        """
        self._get_window_calculator().calc_solar_gains_for_all_windows(
            sun_altitude, sun_azimuth, t_air, hour
        )

    def calc_illuminance_for_all_windows(
            self, sun_altitude: float, sun_azimuth: float, hour: int
    ) -> None:
        """
        Calculates the illuminance in the building zone through the set window
        Args:
            sun_altitude: Altitude Angle of the Sun in Degrees
            sun_azimuth: Azimuth angle of the sun in degrees
            hour: hour to simulate

        Return type:
            None

        """
        self._get_window_calculator().calc_illuminance_for_all_windows(
            sun_altitude, sun_azimuth, hour
        )

    def calc_window_gains_and_illuminance_for_all_windows(
            self,
            sun_altitude: float,
            sun_azimuth: float,
            t_air: float,
            hour: int,
            calculate_illuminance: bool = True,
    ) -> WindowGainsResult:
        """Calculate solar gains + illuminance for all windows in one pass and return named sums."""
        return self._get_window_calculator().calc_window_gains_and_illuminance_for_all_windows(
            sun_altitude,
            sun_azimuth,
            t_air,
            hour,
            calculate_illuminance,
        )

    def _get_occupancy_and_gains_calculator(self) -> OccupancyAndGainsCalculator:
        calculator = getattr(self, "occupancy_and_gains_calculator", None)
        if calculator is None:
            calculator = OccupancyAndGainsCalculator(getattr(self, "building", None))
            self.occupancy_and_gains_calculator = calculator
        return calculator

    def calc_occupancy(
            self, occupancy_schedule: List[ScheduleName], hour: int
    ) -> float:
        """
        Calc occupancy for the time step
        Args:
            occupancy_schedule: schedule name
            hour: hour to simulate

        Returns:
            occupancy
        Return type
            float

        """
        return self._get_occupancy_and_gains_calculator().calc_occupancy(
            occupancy_schedule, hour
        )

    def calc_sum_illuminance_all_windows(self) -> float:
        """
        Sum of transmitted illuminance of all windows
        Returns:
            transmitted illuminance_sum
        Return type
            float

        """
        if not hasattr(self, "window_calculator") and hasattr(self, "all_windows"):
            return sum(element.transmitted_illuminance for element in self.all_windows)
        return self._get_window_calculator().calc_sum_illuminance_all_windows()

    def solve_building_lighting(self, occupancy_percent: float) -> None:
        """
        Calculate the lighting of the building for the time step
        Args:
            occupancy_percent: occupancy for the time step

        Return type:
            None

        """
        self.building.solve_building_lighting(
            self.calc_sum_illuminance_all_windows(), occupancy_percent
        )

    def calc_gains_from_occupancy_and_appliances(
            self,
            occupancy_schedule: List[ScheduleName],
            occupancy: float,
            gain_per_person: float,
            appliance_gains: float,
            hour: int,
    ) -> float:
        """
        Calculate gains from occupancy and appliances
        This is thermal gains. Negative appliance_gains are heat sinks!
        Args:
            occupancy_schedule: schedule name
            occupancy: Occupancy [people]
            gain_per_person:
            appliance_gains:
            hour: hour to simulate

        Returns:
            internal_gains
        Return type
            float

        """
        return self._get_occupancy_and_gains_calculator().calc_gains_from_occupancy_and_appliances(
            occupancy_schedule,
            occupancy,
            gain_per_person,
            appliance_gains,
            hour,
        )

    def calc_appliance_gains_demand(
            self, occupancy_schedule: List[ScheduleName], appliance_gains: float, hour: int
    ) -> float:
        """
        Calculate appliance_gains as part of the internal_gains
        Args:
            occupancy_schedule: schedule name
            appliance_gains:
            hour: hour to simulate

        Returns:
            appliance_gains_demand
        Return type
            float

        """
        return self._get_occupancy_and_gains_calculator().calc_appliance_gains_demand(
            occupancy_schedule, appliance_gains, hour
        )

    def get_appliance_gains_elt_demand(
            self, occupancy_schedule: List[ScheduleName], appliance_gains: float, hour: int
    ) -> float:
        """
        Appliance_gains equal the electric energy that appliances use, except for negative appliance_gains of refrigerated counters in trade buildings for food!
        The assumption is: negative appliance_gains come from referigerated counters with heat pumps for which we assume a COP = 2.
        Args:
            occupancy_schedule: schedule name
            appliance_gains:
            hour: hour to simulate

        Returns:
            appliance_gains_elt_demand
        Return type
            float

        """
        return self._get_occupancy_and_gains_calculator().get_appliance_gains_elt_demand(
            occupancy_schedule, appliance_gains, hour
        )

    def calc_sum_solar_gains_all_windows(self) -> float:
        """
        Sum of solar_gains of all windows
        Returns:
            solar_gains_sum
        Return type
            float

        """
        if not hasattr(self, "window_calculator") and hasattr(self, "all_windows"):
            return sum(element.solar_gains for element in self.all_windows)
        return self._get_window_calculator().calc_sum_solar_gains_all_windows()

    def calc_energy_demand_for_time_step(
            self,
            internal_gains: float,
            t_out: float,
            t_m_prev: float,
            solar_gains_sum: float | None = None,
    ) -> None:
        """
        Calculate energy demand for the time step
        Args:
            internal_gains: internal heat gains from people and appliances [W]
            t_out: Outdoor temperature of this timestep
            t_m_prev:  Previous air temperature [C]

        Return type:
            None

        """
        if solar_gains_sum is None:
            solar_gains_sum = self.calc_sum_solar_gains_all_windows()
        self.building.solve_building_energy(
            internal_gains, solar_gains_sum, t_out, t_m_prev
        )

    def _get_hot_water_calculator(self) -> HotWaterCalculator:
        calculator = getattr(self, "hot_water_calculator", None)
        if calculator is None:
            calculator = HotWaterCalculator(getattr(self, "building", None))
            self.hot_water_calculator = calculator
        return calculator

    def check_if_central_heating_or_central_dhw(self) -> bool:
        """
        Checks if dhw system of the building in the list named central
        Returns:
            True or False
        Return typ
            boolean

        """
        return self._get_hot_water_calculator().has_central_heating_or_dhw()

    def check_if_heat_pump_air_or_ground_source(self) -> bool:
        """
        Checks if dhw system of the building in the list named heat_source
        Returns:
            True or False
        Return typ
            boolean

        """
        return self._get_hot_water_calculator().has_heat_pump_air_or_ground_source()

    def _has_hot_water_system(self) -> bool:
        """Return whether the building has a usable DHW system."""
        return self._get_hot_water_calculator().has_hot_water_system()

    def _calculate_hot_water_demand(
            self, people_share: float, tek_dhw_per_occupancy_full_usage_hour: float
    ) -> float:
        """Calculate domestic hot water demand for one simulation hour."""
        return self._get_hot_water_calculator().calculate_demand(
            people_share, tek_dhw_per_occupancy_full_usage_hour
        )

    def _calculate_hot_water_energy(self, hot_water_demand: float) -> float:
        """Calculate DHW energy using the current heating efficiency when available."""
        return self._get_hot_water_calculator().calculate_energy(hot_water_demand)

    def _uses_electric_hot_water_energy(
            self, central_heating_or_dhw: bool, heat_pump_air_or_ground: bool
    ) -> bool:
        """Return whether DHW energy is assigned to electricity instead of fossils."""
        return self._get_hot_water_calculator().uses_electric_energy(
            central_heating_or_dhw, heat_pump_air_or_ground
        )

    def _split_hot_water_energy_by_system(
            self,
            hot_water_energy: float,
            central_heating_or_dhw: bool,
            heat_pump_air_or_ground: bool,
    ) -> Tuple[float, float]:
        """Split DHW energy into electricity and fossil system energy."""
        return self._get_hot_water_calculator().split_energy_by_system(
            hot_water_energy, central_heating_or_dhw, heat_pump_air_or_ground
        )

    def calc_hot_water_usage(
            self,
            occupancy_schedule: List[ScheduleName],
            tek_dhw_per_occupancy_full_usage_hour: float,
            hour: int,
            people_share: float | None = None,
            has_dhw: bool | None = None,
            central_heating_or_dhw: bool | None = None,
            heat_pump_air_or_ground: bool | None = None,
    ) -> Tuple[float, float, float, float]:
        """
        Calculate hot water usage of the building for the time step with (self.building.heating_energy /
        self.building.heating_demand)
        represents the Efficiency of the heat generation in the building
        Args:
            occupancy_schedule:
            tek_dhw_per_occupancy_full_usage_hour:
            hour:

        Returns:
            hot_water_demand, hot_water_energy, hot_water_sys_electricity, hot_water_sys_fossils
        Return type
            Tuple[float, float, float, float]

        """
        return self._get_hot_water_calculator().calculate_usage(
            occupancy_schedule,
            tek_dhw_per_occupancy_full_usage_hour,
            hour,
            people_share,
            has_dhw,
            central_heating_or_dhw,
            heat_pump_air_or_ground,
        )

    def _get_energy_carrier_resolver(self) -> EnergyCarrierResolver:
        resolver = getattr(self, "energy_carrier_resolver", None)
        if resolver is None:
            resolver = EnergyCarrierResolver(
                getattr(self, "datasource", None),
                getattr(self, "building", None),
            )
            self.energy_carrier_resolver = resolver
        return resolver

    def _get_system_energy_calculator(self) -> SystemEnergyCalculator:
        calculator = getattr(self, "system_energy_calculator", None)
        if calculator is None:
            calculator = SystemEnergyCalculator()
            self.system_energy_calculator = calculator
        return calculator

    def choose_the_fuel_type(self) -> str:
        """Choose the GHG fuel type for the configured heating system."""
        return self._get_energy_carrier_resolver().choose_heating_fuel_type()

    def get_energy_factors(self, fuel_type: str) -> EnergyFactors:
        """Return all configured emission and primary-energy factors for one fuel type."""
        return self._get_energy_carrier_resolver().get_energy_factors(fuel_type)

    def get_ghg_factor_heating(self, fuel_type: str):
        """
        GHG-Factor Heating
        Args:
            fuel_type: fuel_type

        Returns:
            gwp_specific_to_heating_value_GEG
        """
        return self._get_energy_carrier_resolver().get_ghg_factor(fuel_type)

    def get_pe_factor_heating(self, fuel_type: str):
        """
        PE-Factor Heating
        Args:
            fuel_type: fuel_type

        Returns:
            primary_energy_factor_GEG
        """
        return self._get_energy_carrier_resolver().get_primary_energy_factor(fuel_type)

    def get_conversion_factor_heating(self, fuel_type: str):
        """
        Umrechnungsfaktor von Brennwert (Hs) zu Heizwert (Hi) einlesen
        Args:
            fuel_type: fuel_type

        Returns:
            relation_calorific_to_heating_value_GEG
        """
        return self._get_energy_carrier_resolver().get_hs_hi_factor(fuel_type)

    def get_ghg_pe_conversion_factors(self, fuel_type: str) -> EnergyFactors:
        return self.get_energy_factors(fuel_type)

    def _calculate_system_energy_totals(
            self,
            electricity_sum: float,
            fossils_sum: float,
            f_hs_hi: float,
            f_ghg: int,
            f_pe: float,
    ) -> SystemEnergyTotals:
        """Calculate shared Hi, GHG and PE totals for one system energy stream."""
        return self._get_system_energy_calculator().calculate(
            electricity_sum,
            fossils_sum,
            f_hs_hi,
            f_ghg,
            f_pe,
        )

    def check_heating_sys_electricity_sum(
            self,
            calculation_of_sum: CalculationOfSum,
            f_hs_hi: float,
            f_ghg: int,
            f_pe: float,
    ) -> Tuple[int, float, float, float]:
        """

        Args:
            calculation_of_sum: sum object
            f_hs_hi:
            f_ghg:
            f_pe:

        Returns:
            heating_sys_electricity_hi_sum, heating_sys_carbon_sum, heating_sys_pe_sum, heating_sys_fossils_hi_sum
        Return type
            Tuple[int, float, float, float]

        """
        totals = self._calculate_system_energy_totals(
            calculation_of_sum.Heating_Sys_Electricity_sum,
            calculation_of_sum.Heating_Sys_Fossils_sum,
            f_hs_hi,
            f_ghg,
            f_pe,
        )
        return (
            totals.electricity_hi,
            totals.carbon,
            totals.primary_energy,
            totals.fossils_hi,
        )

    def check_hotwater_sys_electricity_sum(
            self,
            calculation_of_sum: CalculationOfSum,
            f_hs_hi: float,
            f_ghg: int,
            f_pe: float,
    ) -> Tuple[int, float, float, float]:
        """

        Args:
            calculation_of_sum: sum object
            f_hs_hi:
            f_ghg:
            f_pe:

        Returns:
            hot_water_sys_electricity_hi_sum, hot_water_sys_pe_sum, hot_water_sys_carbon_sum, hot_water_sys_fossils_hi_sum
        Return type
            Tuple[int, float, float, float]

        """
        totals = self._calculate_system_energy_totals(
            calculation_of_sum.HotWater_Sys_Electricity_sum,
            calculation_of_sum.HotWater_Sys_Fossils_sum,
            f_hs_hi,
            f_ghg,
            f_pe,
        )
        return (
            totals.electricity_hi,
            totals.primary_energy,
            totals.carbon,
            totals.fossils_hi,
        )

    def check_cooling_system_electricity_sum(
            self,
            calculation_of_sum: CalculationOfSum,
            f_hs_hi: float,
            f_ghg: int,
            f_pe: float,
    ) -> Tuple[int, float, float, float]:
        """
        Args:
            calculation_of_sum: sum object
            f_hs_hi:
            f_ghg:
            f_pe:

        Returns:
            cooling_sys_electricity_hi_sum, cooling_sys_carbon_sum, cooling_sys_pe_sum, cooling_sys_fossils_hi_sum
        Return type
            Tuple[int, float, float, float]

        """
        totals = self._calculate_system_energy_totals(
            calculation_of_sum.Cooling_Sys_Electricity_sum,
            calculation_of_sum.Cooling_Sys_Fossils_sum,
            f_hs_hi,
            f_ghg,
            f_pe,
        )
        return (
            totals.electricity_hi,
            totals.carbon,
            totals.primary_energy,
            totals.fossils_hi,
        )

    def sys_electricity_fossils_sum(
            self, system_electricity_hi_sum: int, system_fossils_hi_sum: float
    ) -> float:
        """
        Calculates sum of system_electricity_hi_sum and system_fossils_hi_sum
        Args:
            system_electricity_hi_sum:
            system_fossils_hi_sum:

        Returns:
            system_electricity_hi_sum + system_fossils_hi_sum
        Return type
            float

        """
        return system_electricity_hi_sum + system_fossils_hi_sum

    def hot_energy_hi_sum(
            self, hotWater_sys_electricity_hi_sum: int, hot_water_sys_fossils_hi_sum: float
    ) -> float:
        """
        Calculates sum of hotWater_sys_electricity_hi_sum and hot_water_sys_fossils_hi_sum
        Args:
            hotWater_sys_electricity_hi_sum:
            hot_water_sys_fossils_hi_sum:

        Returns:
            hotWater_sys_electricity_hi_sum + hot_water_sys_fossils_hi_sum
        Return type
            float
        """
        return hotWater_sys_electricity_hi_sum + hot_water_sys_fossils_hi_sum

    def cooling_sys_hi_sum(
            self, cooling_sys_electricity_hi_sum: int, cooling_sys_fossils_hi_sum: float
    ) -> float:
        """
        Calculates sum of cooling_sys_electricity_hi_sum and cooling_sys_fossils_hi_sum
        Args:
            cooling_sys_electricity_hi_sum:
            cooling_sys_fossils_hi_sum:

        Returns:
            cooling_sys_electricity_hi_sum + cooling_sys_fossils_hi_sum
        Return type
            float

        """
        return cooling_sys_electricity_hi_sum + cooling_sys_fossils_hi_sum

    def check_if_central_dhw_use_same_fuel_type_as_heating_system(
            self, fuel_type
    ) -> str:
        """
        Checks if central dhw uses the same fuel type as the heating system
        Assumption: Central DHW-Systems use the same Fuel_type as Heating-Systems, only decentral DHW-Systems might have another Fuel-Type
        Args:
            fuel_type: fuel type

        Returns:
            fuel_type
        Return type
            str

        """

        return self._get_energy_carrier_resolver().choose_hot_water_fuel_type(fuel_type)

    def choose_cooling_energy_fuel_type(self) -> str:
        """Choose the GHG fuel type for the configured cooling system."""
        return self._get_energy_carrier_resolver().choose_cooling_energy_fuel_type()