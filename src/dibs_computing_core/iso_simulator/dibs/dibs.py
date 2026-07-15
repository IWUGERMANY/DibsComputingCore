"""
This class contains the methods that simulate either one building or all buildings
"""
from dibs_computing_core.iso_simulator.data_source.datasource import DataSource
from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.model.hours_result import Result
from dibs_computing_core.iso_simulator.model.ResultOutput import ResultOutput
from dibs_computing_core.iso_simulator.model.summary_result import SummaryResult
from dibs_computing_core.iso_simulator.model.building import Building
from dibs_computing_core.iso_simulator.exceptions import DIBSDataSourceError, DIBSError
import time
import multiprocessing
import logging
import os
from copy import copy
from time import perf_counter

from .dibs_utils.dibs_auxiliary_functions import extracted_method_to_simulate_one_building, unpack_results


logger = logging.getLogger(__name__)

PERF_LOG_TRUE_VALUES = {"1", "true", "yes", "on"}


def _perf_logging_enabled() -> bool:
    """Return whether structured SIM_PERF logs should be emitted."""
    return os.getenv("DIBS_PERF_LOG", "").lower() in PERF_LOG_TRUE_VALUES


def _log_perf(phase: str, duration_s: float) -> None:
    """Emit a structured performance log only when explicitly enabled."""
    if _perf_logging_enabled():
        logger.info("SIM_PERF dibs phase=%s duration_s=%.4f", phase, duration_s)


def _add_worker_error_context(
    error: DIBSError, building: Building, phase: str
) -> None:
    if error.phase is None:
        error.phase = phase
    error.context.setdefault(
        "building_id", getattr(building, "scr_gebaeude_id", None)
    )


def _simulate_building_worker(
    datasource: DataSource, building: Building
) -> tuple[Result, ResultOutput]:
    """Simulate one building with an isolated DataSource copy."""
    datasource.building = building
    try:
        datasource.get_epw_file()
    except DIBSError as error:
        _add_worker_error_context(error, building, "initialize_data")
        raise

    try:
        simulator = BuildingSimulator(datasource)
    except DIBSError as error:
        _add_worker_error_context(error, building, "simulator_init")
        raise

    try:
        return extracted_method_to_simulate_one_building(
            simulator, building.t_set_heating
        )
    except DIBSError as error:
        _add_worker_error_context(error, building, "simulate_hours")
        raise


def _pool_size(task_count: int) -> int:
    """Avoid starting more worker processes than there are building tasks."""
    return min(task_count, multiprocessing.cpu_count() or 1)


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

    @staticmethod
    def _run_with_error_phase(phase: str, operation, *args):
        """Run one phase and enrich expected DIBS errors with its name."""
        try:
            return operation(*args)
        except DIBSError as error:
            if error.phase is None:
                error.phase = phase
            raise

    def calculate_result_of_one_building(self) -> tuple[float, Result, SummaryResult]:
        """Simulate one building and propagate expected DIBS failures."""
        perf_logging = _perf_logging_enabled()
        total_started = perf_counter() if perf_logging else None

        user_args = self._run_with_error_phase(
            "initialize_data", self.get_user_args
        )

        started = perf_counter() if perf_logging else None
        self._run_with_error_phase("initialize_data", self.initialize_data)
        self._validate_datasource_state()
        if perf_logging:
            _log_perf("initialize_data", perf_counter() - started)

        started = perf_counter() if perf_logging else None
        simulator = self._run_with_error_phase(
            "simulator_init", BuildingSimulator, self.datasource
        )
        if perf_logging:
            _log_perf("simulator_init", perf_counter() - started)

        t_set_heating_temp = simulator.datasource.building.t_set_heating
        started = perf_counter()
        result, result_output = self._run_with_error_phase(
            "simulate_hours",
            extracted_method_to_simulate_one_building,
            simulator,
            t_set_heating_temp,
        )
        simulation_time = perf_counter() - started
        if perf_logging:
            _log_perf("simulate_hours", simulation_time)

        started = perf_counter() if perf_logging else None
        summary_result = self._run_with_error_phase(
            "summary_wrap", SummaryResult, result_output, user_args
        )
        if perf_logging:
            _log_perf("summary_wrap", perf_counter() - started)
            _log_perf("total", perf_counter() - total_started)
        return simulation_time, result, summary_result
    def initialize_data(self):
        self.datasource.get_user_building()
        self.datasource.get_epw_pe_factors()
        self.datasource.get_epw_file()

    def _validate_datasource_state(self) -> None:
        """Ensure that stateful DataSource initialization produced all inputs."""
        required_fields = ("building", "epw_file", "epw_pe_factors")
        missing_fields = [
            field
            for field in required_fields
            if getattr(self.datasource, field, None) is None
        ]
        if missing_fields:
            raise DIBSDataSourceError(
                "DataSource initialization is incomplete",
                phase="initialize_data",
                context={"missing_fields": missing_fields},
            )

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

    def _worker_datasource_copy(self) -> DataSource:
        """Copy shared configuration without retaining the full building stock."""
        datasource = copy(self.datasource)
        datasource.building = None
        datasource.buildings = None
        return datasource

    def multi(self) -> tuple[float, list[Result], list[SummaryResult]]:
        """
        Simulates all buildings parallel using multiprocessing.Pool()
        Parameters

        Returns
            (simulation_time, results_all_hours, summary_results)
        """
        user_args = self.get_user_args()
        self.datasource.get_user_buildings()
        self.datasource.get_epw_pe_factors()
        if not self.datasource.buildings:
            return 0.0, [], []

        begin = time.time()
        worker_datasource = self._worker_datasource_copy()
        with multiprocessing.Pool(
            processes=_pool_size(len(self.datasource.buildings))
        ) as pool:
            async_results = [
                pool.apply_async(
                    _simulate_building_worker, (worker_datasource, building)
                )
                for building in self.datasource.buildings
            ]
            results = [result.get() for result in async_results]
            simulation_time = time.time() - begin

            result, result_output = unpack_results(results)

            summary_results = [SummaryResult(result, user_args) for result in result_output]

        return simulation_time, result, summary_results

    def multi_with_batches(
        self, user_args, buildings, start, end, batch_results=None
    ) -> tuple[float, list[Result], list[SummaryResult]]:
        """
        Simulates all buildings parallel using multiprocessing.Pool()
        Parameters

        Returns
            (simulation_time, results_all_hours, summary_results)
        """

        selected_buildings = buildings[start:end]
        if not selected_buildings:
            return 0.0, [], []

        begin = time.time()
        worker_datasource = self._worker_datasource_copy()
        with multiprocessing.Pool(
            processes=_pool_size(len(selected_buildings))
        ) as pool:
            async_results = [
                pool.apply_async(
                    _simulate_building_worker, (worker_datasource, building)
                )
                for building in selected_buildings
            ]
            results = [result.get() for result in async_results]
            simulation_time = time.time() - begin

            result, result_output = unpack_results(results)

            summary_results = [SummaryResult(result, user_args) for result in result_output]

        return simulation_time, result, summary_results
