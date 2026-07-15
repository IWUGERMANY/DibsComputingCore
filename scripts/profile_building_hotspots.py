"""Profile Building hot-path methods for the 9-building CSV scenario.

Usage from the DibsComputingCore root:

    python scripts/profile_building_hotspots.py

The script runs the same CSV/DataSource path as the golden regression and records
method-level call counts and wall time for selected Building hotloop methods.
It intentionally profiles a sequential all-buildings path in the parent process;
DIBS.multi() uses multiprocessing, where parent-process monkeypatch counters would
otherwise stay at zero.
It does not change simulation formulas or results.
"""

from __future__ import annotations

import argparse
import functools
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SRC = PROJECT_ROOT / "src"
STAND_DIBS_ROOT = PROJECT_ROOT.parent
DEFAULT_INPUT = STAND_DIBS_ROOT / "SimulationData_Breitenerhebung.csv"
DEFAULT_DATASOURCE_CSV_SRC = STAND_DIBS_ROOT / "DibsDataSourceCSV" / "src"
DEFAULT_DIBS_DATA_SRC = STAND_DIBS_ROOT / "DibsData" / "src"
DEFAULT_OUTPUT = PROJECT_ROOT / "performance_results" / "building_hotspot_profile.csv"

BUILDING_METHODS = (
    "calc_h_ve_adj",
    "check_night_flushing",
    "solve_building_lighting",
    "solve_building_energy",
    "has_demand",
    "calc_temperatures_crank_nicolson",
    "calc_energy_demand",
    "calc_energy_demand_unrestricted",
    "calc_heat_flow",
)


@dataclass
class MethodStats:
    calls: int = 0
    total_s: float = 0.0
    max_s: float = 0.0

    def record(self, elapsed_s: float) -> None:
        self.calls += 1
        self.total_s += elapsed_s
        if elapsed_s > self.max_s:
            self.max_s = elapsed_s

    @property
    def avg_us(self) -> float:
        if self.calls == 0:
            return 0.0
        return (self.total_s / self.calls) * 1_000_000.0


def _add_optional_source_path(path: Path) -> None:
    if path.exists():
        sys.path.insert(0, str(path))


def _wrap_method(cls: type, method_name: str, stats: dict[str, MethodStats]) -> None:
    original = getattr(cls, method_name)

    @functools.wraps(original)
    def wrapper(self, *args, **kwargs):
        start = perf_counter()
        try:
            return original(self, *args, **kwargs)
        finally:
            stats[method_name].record(perf_counter() - start)

    setattr(cls, method_name, wrapper)


def _install_building_profilers() -> dict[str, MethodStats]:
    from dibs_computing_core.iso_simulator.model.building import Building

    stats = {method_name: MethodStats() for method_name in BUILDING_METHODS}
    for method_name in BUILDING_METHODS:
        _wrap_method(Building, method_name, stats)
    return stats


def _run_simulation(input_csv: Path, datasource_csv_src: Path, dibs_data_src: Path):
    _add_optional_source_path(PROJECT_SRC)
    _add_optional_source_path(datasource_csv_src)
    _add_optional_source_path(dibs_data_src)

    from dibs_datasource_csv.datasource_csv import DataSourceCSV
    from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
    from dibs_computing_core.iso_simulator.model.summary_result import SummaryResult

    stats = _install_building_profilers()
    datasource = DataSourceCSV(
        str(input_csv),
        "din18599",
        "mid",
        "sia2024",
        "2004-2018",
        "GEG",
    )
    dibs = DIBS(datasource)

    # Use the same datasource initialization as DIBS.multi(), but keep the hourly
    # simulation in this process. multiprocessing workers would hide monkeypatch
    # counters from this profiling script.
    user_args = dibs.get_user_args()
    datasource.get_user_buildings()
    datasource.get_epw_pe_factors()

    start = perf_counter()
    result_outputs = []
    for index in range(len(datasource.buildings)):
        _result, result_output = dibs.calculate_result_of_all_buildings(
            datasource.buildings, index
        )
        result_outputs.append(result_output)
    simulation_time_s = perf_counter() - start
    summaries = [SummaryResult(result_output, user_args) for result_output in result_outputs]
    wall_time_s = perf_counter() - start
    return stats, simulation_time_s, wall_time_s, len(summaries)


def _stats_dataframe(stats: dict[str, MethodStats]) -> pd.DataFrame:
    total_profiled_s = sum(method_stats.total_s for method_stats in stats.values())
    rows = []
    for method_name, method_stats in stats.items():
        share = (
            method_stats.total_s / total_profiled_s if total_profiled_s > 0 else 0.0
        )
        rows.append(
            {
                "method": method_name,
                "calls": method_stats.calls,
                "total_s": method_stats.total_s,
                "avg_us": method_stats.avg_us,
                "max_us": method_stats.max_s * 1_000_000.0,
                "share_of_profiled_time": share,
            }
        )
    dataframe = pd.DataFrame(rows)
    return dataframe.sort_values("total_s", ascending=False).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--datasource-csv-src", type=Path, default=DEFAULT_DATASOURCE_CSV_SRC)
    parser.add_argument("--dibs-data-src", type=Path, default=DEFAULT_DIBS_DATA_SRC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    stats, simulation_time_s, wall_time_s, building_count = _run_simulation(
        args.input,
        args.datasource_csv_src,
        args.dibs_data_src,
    )
    dataframe = _stats_dataframe(stats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(args.output, index=False)

    print(f"buildings={building_count}")
    print(f"simulation_time_s={simulation_time_s:.6f} wall_time_s={wall_time_s:.6f}")
    print(f"profile_file={args.output}")
    print(dataframe.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
