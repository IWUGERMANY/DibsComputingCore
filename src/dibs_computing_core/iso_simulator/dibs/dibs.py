"""
This class contains the methods that simulate either one building or all buildings
"""
from dibs_computing_core.iso_simulator.data_source.datasource import DataSource
from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.model.hours_result import Result
from dibs_computing_core.iso_simulator.model.ResultOutput import ResultOutput
from dibs_computing_core.iso_simulator.model.summary_result import SummaryResult
from dibs_computing_core.iso_simulator.model.building import Building
import time
import multiprocessing
from typing import List

from .dibs_utils.dibs_auxiliary_functions import extracted_method_to_simulate_one_building, unpack_results


class DIBS:
    def __init__(self, datasource: DataSource):
        """
        This constructor to initialize an instance of the DIBS class
        Args:
            datasource: object which can deal with several data format (csv file, JSON, database, etc...)
        """
        self.datasource = datasource

    def set_data_source(self, datasource: DataSource):
        self.datasource = datasource

    def calculate_result_of_one_building(self) -> tuple[float, Result, SummaryResult]:
        """
        This method simulates the building which located in the given path
        Args:

        Returns:

        """
        time_begin = time.time()

        user_args = self.get_user_args()

        self.initialize_data()

        simulator = BuildingSimulator(self.datasource)

        t_set_heating_temp = simulator.datasource.building.t_set_heating

        result, result_output = extracted_method_to_simulate_one_building(
            simulator, t_set_heating_temp)
        simulation_time = time.time() - time_begin
        return simulation_time, result, SummaryResult(result_output, user_args)

    def initialize_data(self):
        self.datasource.get_user_building()
        self.datasource.get_epw_pe_factors()
        self.datasource.get_epw_file()

    def get_user_args(self):
        return [self.datasource.profile_from_norm,
                self.datasource.gains_from_group_values,
                self.datasource.usage_from_norm,
                self.datasource.weather_period]

    def calculate_result_of_all_buildings(self, user_buildings: list[Building], index: int) -> tuple[
        Result, ResultOutput]:
        """
        Simulate one building
        Parameters
        user_buildings:
            index: index of the building

        Returns
            (result, result_output)
        """
        user_args = self.get_user_args()

        self.datasource.building = user_buildings[index]
        self.datasource.get_epw_file()

        simulator = BuildingSimulator(self.datasource)

        t_set_heating_temp = user_buildings[index].t_set_heating

        result, result_output = extracted_method_to_simulate_one_building(
            simulator, t_set_heating_temp
        )

        return result, result_output

    def multi(self) -> tuple[float, Result: List[Result], List[SummaryResult]]:
        """
        Simulates all buildings parallel using multiprocessing.Pool()
        Parameters

        Returns
            (simulation_time, results_all_hours, summary_results)
        """
        user_args = self.get_user_args()

        self.datasource.get_user_buildings()
        self.datasource.get_epw_pe_factors()

        with multiprocessing.Pool() as pool:
            results = []
            begin = time.time()

            for index, building in enumerate(self.datasource.buildings):
                result = pool.apply_async(
                    self.calculate_result_of_all_buildings,
                    (self.datasource.buildings, index)
                )
                results.append(result)

            pool.close()
            pool.join()

            results = [result.get() for result in results]
            end = time.time()
            simulation_time = end - begin

            result, result_output = unpack_results(results)

            summary_results = [SummaryResult(result, user_args) for result in result_output]

        return simulation_time, result, summary_results
