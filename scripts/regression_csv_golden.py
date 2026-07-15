"""Golden regression runner for the 9-building CSV DIBS simulation.

Usage from the DibsComputingCore root:

    python scripts/regression_csv_golden.py --update-golden
    python scripts/regression_csv_golden.py

The first command creates/updates the golden CSV files. The second command runs the
simulation again and compares all SummaryResult fields plus selected hourly values.
"""

from __future__ import annotations

import argparse
import math
import sys
from numbers import Real
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SRC = PROJECT_ROOT / "src"
STAND_DIBS_ROOT = PROJECT_ROOT.parent
DEFAULT_INPUT = STAND_DIBS_ROOT / "SimulationData_Breitenerhebung.csv"
DEFAULT_DATASOURCE_CSV_SRC = STAND_DIBS_ROOT / "DibsDataSourceCSV" / "src"
DEFAULT_DIBS_DATA_SRC = STAND_DIBS_ROOT / "DibsData" / "src"
DEFAULT_GOLDEN = PROJECT_ROOT / "tests" / "golden" / "summary_9_buildings.csv"
DEFAULT_HOURLY_GOLDEN = PROJECT_ROOT / "tests" / "golden" / "hourly_sample_9_buildings.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "regression_results"
HOURLY_SAMPLE_HOURS = (0, 1, 8, 12, 18, 8759)
HOURLY_SAMPLE_FIELDS = (
    "heating_demand",
    "cooling_demand",
    "all_hot_water_demand",
    "temp_air",
    "outside_temp",
    "lighting_demand",
    "internal_gains",
    "solar_gains_total",
)


def _add_optional_source_path(path: Path) -> None:
    if path.exists():
        sys.path.insert(0, str(path))


def _normalize_cell(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return value[0] if len(value) == 1 else str(value)
    return value


def _summary_dataframe(summaries: list[Any]) -> pd.DataFrame:
    rows = []
    for summary in summaries:
        rows.append({key: _normalize_cell(value) for key, value in vars(summary).items()})
    dataframe = pd.DataFrame(rows)
    if "building_id" in dataframe.columns:
        dataframe = dataframe.sort_values("building_id").reset_index(drop=True)
    return dataframe

def _hourly_sample_dataframe(results: list[Any], summaries: list[Any]) -> pd.DataFrame:
    """Return selected hourly values for a compact hotloop regression check."""
    rows = []
    building_ids = [getattr(summary, "building_id", index) for index, summary in enumerate(summaries)]
    for building_index, result in enumerate(results):
        building_id = building_ids[building_index]
        for hour in HOURLY_SAMPLE_HOURS:
            row = {"building_id": building_id, "hour": hour}
            for field in HOURLY_SAMPLE_FIELDS:
                values = getattr(result, field)
                row[field] = values[hour]
            rows.append(row)
    dataframe = pd.DataFrame(rows)
    if not dataframe.empty:
        dataframe = dataframe.sort_values(["building_id", "hour"]).reset_index(drop=True)
    return dataframe


def _run_simulation(
    input_csv: Path,
    datasource_csv_src: Path,
    dibs_data_src: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    _add_optional_source_path(PROJECT_SRC)
    _add_optional_source_path(datasource_csv_src)
    _add_optional_source_path(dibs_data_src)

    from dibs_datasource_csv.datasource_csv import DataSourceCSV
    from dibs_computing_core.iso_simulator.dibs.dibs import DIBS

    datasource = DataSourceCSV(
        str(input_csv),
        "din18599",
        "mid",
        "sia2024",
        "2004-2018",
        "GEG",
    )
    start = perf_counter()
    simulation_time_s, hourly_results, summaries = DIBS(datasource).multi()
    wall_time_s = perf_counter() - start
    return (
        _summary_dataframe(summaries),
        _hourly_sample_dataframe(hourly_results, summaries),
        simulation_time_s,
        wall_time_s,
    )


def _values_equal(golden_value: Any, current_value: Any, tolerance: float) -> bool:
    if pd.isna(golden_value) and pd.isna(current_value):
        return True
    if isinstance(golden_value, Real) and isinstance(current_value, Real):
        return math.isclose(
            float(golden_value),
            float(current_value),
            rel_tol=tolerance,
            abs_tol=tolerance,
        )
    return str(golden_value) == str(current_value)


def _compare(golden: pd.DataFrame, current: pd.DataFrame, tolerance: float) -> pd.DataFrame:
    diff_rows = []
    golden_columns = list(golden.columns)
    current_columns = list(current.columns)

    for column in sorted(set(golden_columns) - set(current_columns)):
        diff_rows.append(
            {"building_id": None, "field": column, "problem": "missing_in_current"}
        )
    for column in sorted(set(current_columns) - set(golden_columns)):
        diff_rows.append(
            {"building_id": None, "field": column, "problem": "new_in_current"}
        )

    shared_columns = [column for column in golden_columns if column in current_columns]
    row_count = min(len(golden), len(current))

    if len(golden) != len(current):
        diff_rows.append(
            {
                "building_id": None,
                "field": "<row_count>",
                "problem": "row_count_changed",
                "golden_value": len(golden),
                "current_value": len(current),
            }
        )

    for index in range(row_count):
        building_id = current.iloc[index].get("building_id", index)
        for column in shared_columns:
            golden_value = golden.iloc[index][column]
            current_value = current.iloc[index][column]
            if _values_equal(golden_value, current_value, tolerance):
                continue
            diff_rows.append(
                {
                    "building_id": building_id,
                    "field": column,
                    "problem": "value_changed",
                    "golden_value": golden_value,
                    "current_value": current_value,
                    "abs_diff": _abs_diff(golden_value, current_value),
                }
            )
    return pd.DataFrame(diff_rows)


def _abs_diff(left: Any, right: Any) -> float | None:
    if isinstance(left, Real) and isinstance(right, Real):
        if pd.isna(left) or pd.isna(right):
            return None
        return abs(float(left) - float(right))
    return None


def _write_outputs(
    output_dir: Path,
    current: pd.DataFrame,
    diff: pd.DataFrame,
    hourly_current: pd.DataFrame,
    hourly_diff: pd.DataFrame,
    simulation_time_s: float,
    wall_time_s: float,
    tolerance: float,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "summary_9_buildings_comparison.xlsx"
    metadata = pd.DataFrame(
        {
            "property": [
                "buildings",
                "fields",
                "summary_differences",
                "hourly_differences",
                "differences",
                "hourly_rows",
                "simulation_time_s",
                "wall_time_s",
                "tolerance",
            ],
            "value": [
                len(current),
                len(current.columns),
                len(diff),
                len(hourly_diff),
                len(diff) + len(hourly_diff),
                len(hourly_current),
                simulation_time_s,
                wall_time_s,
                tolerance,
            ],
        }
    )
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        metadata.to_excel(writer, sheet_name="Metadata", index=False)
        current.to_excel(writer, sheet_name="Current", index=False)
        diff.to_excel(writer, sheet_name="Diff", index=False)
        hourly_current.to_excel(writer, sheet_name="HourlyCurrent", index=False)
        hourly_diff.to_excel(writer, sheet_name="HourlyDiff", index=False)
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run and compare the 9-building DIBS CSV golden regression."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--datasource-csv-src", type=Path, default=DEFAULT_DATASOURCE_CSV_SRC)
    parser.add_argument("--dibs-data-src", type=Path, default=DEFAULT_DIBS_DATA_SRC)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument(
        "--hourly-golden", type=Path, default=DEFAULT_HOURLY_GOLDEN
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--update-golden", action="store_true")
    args = parser.parse_args()

    current, hourly_current, simulation_time_s, wall_time_s = _run_simulation(
        args.input,
        args.datasource_csv_src,
        args.dibs_data_src,
    )

    if args.update_golden:
        args.golden.parent.mkdir(parents=True, exist_ok=True)
        args.hourly_golden.parent.mkdir(parents=True, exist_ok=True)
        current.to_csv(args.golden, index=False)
        hourly_current.to_csv(args.hourly_golden, index=False)
        print(f"golden_updated={args.golden}")
        print(f"hourly_golden_updated={args.hourly_golden}")
        print(
            f"buildings={len(current)} fields={len(current.columns)} "
            f"hourly_rows={len(hourly_current)} "
            f"simulation_time_s={simulation_time_s:.6f} wall_time_s={wall_time_s:.6f}"
        )
        return 0

    missing_goldens = [
        path for path in (args.golden, args.hourly_golden) if not path.exists()
    ]
    if missing_goldens:
        for missing_golden in missing_goldens:
            print(f"golden_missing={missing_golden}")
        print("Create them first with: python scripts/regression_csv_golden.py --update-golden")
        return 2

    golden = pd.read_csv(args.golden, keep_default_na=False)
    hourly_golden = pd.read_csv(args.hourly_golden, keep_default_na=False)
    diff = _compare(golden, current, args.tolerance)
    hourly_diff = _compare(hourly_golden, hourly_current, args.tolerance)
    output_file = _write_outputs(
        args.output_dir,
        current,
        diff,
        hourly_current,
        hourly_diff,
        simulation_time_s,
        wall_time_s,
        args.tolerance,
    )

    total_differences = len(diff) + len(hourly_diff)
    print(
        f"buildings={len(current)} fields={len(current.columns)} "
        f"hourly_rows={len(hourly_current)} differences={total_differences}"
    )
    print(f"summary_differences={len(diff)} hourly_differences={len(hourly_diff)}")
    print(f"simulation_time_s={simulation_time_s:.6f} wall_time_s={wall_time_s:.6f}")
    print(f"comparison_file={output_file}")
    return 0 if diff.empty and hourly_diff.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())