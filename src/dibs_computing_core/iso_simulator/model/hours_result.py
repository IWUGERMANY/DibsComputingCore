from .building import Building
from .calculations_sum import CalculationOfSum
from .window import Window


class Result:
    """
    Stores the hourly result series for the calculation of a building.
    """

    SUM_SERIES = {
        "HeatingDemand": "heating_demand",
        "HeatingEnergy": "heating_energy",
        "Heating_Sys_Electricity": "heating_sys_electricity",
        "Heating_Sys_Fossils": "heating_sys_fossils",
        "CoolingDemand": "cooling_demand",
        "CoolingEnergy": "cooling_energy",
        "Cooling_Sys_Electricity": "cooling_sys_electricity",
        "Cooling_Sys_Fossils": "cooling_sys_fossils",
        "HotWaterDemand": "all_hot_water_demand",
        "HotWaterEnergy": "all_hot_water_energy",
        "HotWater_Sys_Electricity": "hot_water_sys_electricity",
        "HotWater_Sys_Fossils": "hot_water_sys_fossils",
        "ElectricityDemandTotal": "electricity_demand_total",
        "InternalGains": "internal_gains",
        "Appliance_gains_demand": "appliance_gains_demand",
        "Appliance_gains_elt_demand": "appliance_gains_elt_demand",
        "LightingDemand": "lighting_demand",
        "SolarGainsSouthWindow": "solar_gains_south_window",
        "SolarGainsEastWindow": "solar_gains_east_window",
        "SolarGainsWestWindow": "solar_gains_west_window",
        "SolarGainsNorthWindow": "solar_gains_north_window",
        "SolarGainsTotal": "solar_gains_total",
        "TransmissionLoss": "transmission_loss",
        "VentilationLoss": "ventilation_loss",
    }

    MEAN_SERIES = {
        "OccupancyProfilePeople": "occupancy_profile_people",
        "ApplianceProfileFactor": "appliance_profile_factor",
        "AirChangeRateEffective": "air_change_rate_effective",
        "AirFlowRateEffective": "air_flow_rate_effective",
    }

    def __init__(self):
        self.heating_demand = []
        self.heating_energy = []
        self.heating_sys_electricity = []
        self.heating_sys_fossils = []
        self.cooling_demand = []
        self.cooling_energy = []
        self.cooling_sys_electricity = []
        self.cooling_sys_fossils = []
        self.all_hot_water_demand = []
        self.all_hot_water_energy = []
        self.hot_water_sys_electricity = []
        self.hot_water_sys_fossils = []
        self.electricity_demand_total = []
        self.temp_air = []
        self.outside_temp = []
        self.lighting_demand = []
        self.internal_gains = []
        self.solar_gains_south_window = []
        self.solar_gains_east_window = []
        self.solar_gains_west_window = []
        self.solar_gains_north_window = []
        self.solar_gains_total = []
        self.DayTime = []
        self.appliance_gains_demand = []
        self.appliance_gains_elt_demand = []
        self.transmission_loss = []
        self.ventilation_loss = []
        self.is_heating_period_hour = []
        self.occupancy_profile_people = []
        self.appliance_profile_factor = []
        self.air_change_rate_effective = []
        self.air_flow_rate_effective = []

    def append_results(
            self,
            building: Building,
            all_windows: list[Window],
            hot_water_demand: float,
            hot_water_energy: float,
            hot_water_sys_electricity: float,
            hot_water_sys_fossils: float,
            t_out: float,
            internal_gains: float,
            appliance_gains_demand: float,
            appliance_gains_elt_demand: float,
            solar_gains_all_windows: float,
            hour: int,
            electricity_demand_total: float = 0.0,
            transmission_loss: float = 0.0,
            ventilation_loss: float = 0.0,
            is_heating_period_hour: bool = False,
            occupancy_profile_people: float = 0.0,
            appliance_profile_factor: float = 0.0,
            air_change_rate_effective: float = 0.0,
            air_flow_rate_effective: float = 0.0,
    ) -> None:
        """
        Appends the result of a simulated hour to the result object.
        """
        windows = all_windows

        self.heating_demand.append(building.heating_demand)
        self.heating_energy.append(building.heating_energy)
        self.heating_sys_electricity.append(building.heating_sys_electricity)
        self.heating_sys_fossils.append(building.heating_sys_fossils)
        self.cooling_demand.append(building.cooling_demand)
        self.cooling_energy.append(building.cooling_energy)
        self.cooling_sys_electricity.append(building.cooling_sys_electricity)
        self.cooling_sys_fossils.append(building.cooling_sys_fossils)
        self.all_hot_water_demand.append(hot_water_demand)
        self.all_hot_water_energy.append(hot_water_energy)
        self.hot_water_sys_electricity.append(hot_water_sys_electricity)
        self.hot_water_sys_fossils.append(hot_water_sys_fossils)
        self.electricity_demand_total.append(electricity_demand_total)
        self.temp_air.append(building.t_air)
        self.outside_temp.append(t_out)
        self.lighting_demand.append(building.lighting_demand)
        self.internal_gains.append(internal_gains)
        self.solar_gains_south_window.append(windows[0].solar_gains)
        self.solar_gains_east_window.append(windows[1].solar_gains)
        self.solar_gains_west_window.append(windows[2].solar_gains)
        self.solar_gains_north_window.append(windows[3].solar_gains)
        self.solar_gains_total.append(solar_gains_all_windows)
        self.DayTime.append(hour % 24)
        self.appliance_gains_demand.append(appliance_gains_demand)
        self.appliance_gains_elt_demand.append(appliance_gains_elt_demand)
        self.transmission_loss.append(transmission_loss)
        self.ventilation_loss.append(ventilation_loss)
        self.is_heating_period_hour.append(is_heating_period_hour)
        self.occupancy_profile_people.append(occupancy_profile_people)
        self.appliance_profile_factor.append(appliance_profile_factor)
        self.air_change_rate_effective.append(air_change_rate_effective)
        self.air_flow_rate_effective.append(air_flow_rate_effective)

    @staticmethod
    def _sum_to_kwh(values: list[float]) -> float:
        return sum(values) * 0.001

    def _select_heating_period(self, values: list[float]) -> list[float]:
        return [
            value
            for value, is_heating_hour in zip(values, self.is_heating_period_hour)
            if is_heating_hour
        ]

    @staticmethod
    def _mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def calc_sum_of_results(self, weather_metrics: dict | None = None) -> CalculationOfSum:
        """
        Calculates annual and heating-period aggregates for all result series.
        """
        results = {}

        for name, attr_name in self.SUM_SERIES.items():
            values = getattr(self, attr_name)
            results[f"{name}_sum"] = self._sum_to_kwh(values)
            results[f"HeatingPeriod{name}_sum"] = self._sum_to_kwh(
                self._select_heating_period(values)
            )

        for name, attr_name in self.MEAN_SERIES.items():
            values = getattr(self, attr_name)
            results[f"{name}_mean"] = self._mean(values)
            results[f"HeatingPeriod{name}_mean"] = self._mean(
                self._select_heating_period(values)
            )

        results["HeatingPeriodHours"] = sum(
            1 for is_heating_hour in self.is_heating_period_hour if is_heating_hour
        )

        if weather_metrics:
            results.update(weather_metrics)

        return CalculationOfSum(**results)

    def __str__(self):
        attrs = "\n".join([f"{key} = {getattr(self, key)}" for key in vars(self)])
        return f"Result of all hours: {attrs}"
