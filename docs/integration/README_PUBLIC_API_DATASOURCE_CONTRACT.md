# DIBS Public API and DataSource Contract

## Purpose

This document defines the integration contract between `DibsComputingCore` and host data providers such as `DibsDataSourceCSV`, `DataSourceDjango` and Lezbau.

The core is intentionally data-source neutral: it does not know whether input comes from CSV, Django, an API, or tests. Host layers must provide the stateful `DataSource` interface described here.

## Stable Public Entry Points

### `DIBS(datasource)`

Creates a DIBS simulation facade around one `DataSource` implementation.

```python
from dibs_computing_core.iso_simulator.dibs.dibs import DIBS

runner = DIBS(datasource)
```

The `datasource` object must implement `dibs_computing_core.iso_simulator.data_source.datasource.DataSource`.

### `calculate_result_of_one_building()`

Simulates one building.

```python
simulation_time, hourly_result, summary_result = runner.calculate_result_of_one_building()
```

Return contract:

- `simulation_time`: `float`, seconds spent in the hourly simulation phase.
- `hourly_result`: `Result`, hourly result container.
- `summary_result`: `SummaryResult`, annual/summary result wrapper.

Internal phase order:

```text
get_user_args()
initialize_data()
  -> datasource.get_user_building()
  -> datasource.get_epw_pe_factors()
  -> datasource.get_epw_file()
_validate_datasource_state()
BuildingSimulator(datasource)
extracted_method_to_simulate_one_building(...)
SummaryResult(...)
```

After `initialize_data()`, the datasource must contain at least:

- `datasource.building`
- `datasource.epw_file`
- `datasource.epw_pe_factors`

If one of these is missing, DIBS raises `DIBSDataSourceError` with phase `initialize_data`.

### `multi()`

Simulates all buildings available from the datasource using multiprocessing.

```python
simulation_time, hourly_results, summary_results = runner.multi()
```

Return contract:

- `simulation_time`: `float`
- `hourly_results`: `list[Result]`
- `summary_results`: `list[SummaryResult]`

Internal phase order:

```text
get_user_args()
datasource.get_user_buildings()
datasource.get_epw_pe_factors()
for each building in multiprocessing worker:
  worker_datasource.building = building
  worker_datasource.get_epw_file()
  BuildingSimulator(worker_datasource)
  extracted_method_to_simulate_one_building(...)
SummaryResult(...) for each result output
```

If `datasource.buildings` is empty, `multi()` returns:

```python
(0.0, [], [])
```

### `multi_with_batches(user_args, buildings, start, end, batch_results=None)`

Simulates a slice of an existing building list using multiprocessing.

```python
simulation_time, hourly_results, summary_results = runner.multi_with_batches(
    user_args=user_args,
    buildings=buildings,
    start=0,
    end=100,
)
```

This method expects `buildings` to already contain `Building` objects. It does not call `get_user_buildings()` itself.

## Required DataSource Methods

Every datasource implementation must provide the abstract methods from `DataSource`.

| Method | Required behavior |
| --- | --- |
| `get_user_building()` | Load one `Building` and assign it to `self.building`. |
| `get_user_buildings()` | Load all `Building` objects and assign them to `self.buildings`. |
| `get_epw_pe_factors()` | Load primary-energy and emission factors and assign them to `self.epw_pe_factors`. |
| `get_epw_file()` | Resolve the weather/EPW metadata for `self.building` and assign it to `self.epw_file`. |
| `choose_and_get_the_right_weather_data_from_path()` | Return weather data for the current building/weather selection. |
| `get_schedule()` | Return `(schedule_names, profile_name, profile_factor)`. |
| `get_tek()` | Return `(tek_value, tek_name)`. |
| `get_usage_time()` | Return `(usage_start, usage_end)`. |
| `get_gains()` | Return `(gain_person_and_typ_norm, appliance_gains)`. |

## Required DataSource State

The core accesses the following datasource attributes directly.

### Input selection attributes

These are used by `DIBS.get_user_args()` and are passed into `SummaryResult`.

| Attribute | Meaning |
| --- | --- |
| `profile_from_norm` | Profile source/selection. |
| `gains_from_group_values` | Internal gains source/selection. |
| `usage_from_norm` | Usage-time source/selection. |
| `weather_period` | Weather period selection. |

### Runtime state attributes

| Attribute | Required after | Meaning |
| --- | --- | --- |
| `building` | `get_user_building()` or worker setup | Current `Building` object. |
| `buildings` | `get_user_buildings()` | List of `Building` objects for batch simulation. |
| `epw_file` | `get_epw_file()` | Selected EPW metadata/file object. |
| `epw_pe_factors` | `get_epw_pe_factors()` | Primary-energy/emission factor data. |

## Expected Model Objects

DataSource implementations should construct and return the core model classes, not dictionaries.

Expected core model classes include:

- `Building`
- `EPWFile`
- `PrimaryEnergyAndEmissionFactor`
- `ScheduleName`
- `WeatherData`

The public boundary stays object-based. DataFrames, raw CSV rows, Django models and API payloads should be normalized inside the datasource implementation before entering DIBS core simulation.

## Error Contract

Expected host-visible errors must inherit from `DIBSError`.

Common errors:

| Exception | Code | Typical phase |
| --- | --- | --- |
| `DIBSDataSourceError` | `DIBS_DATASOURCE_ERROR` | `initialize_data` |
| `PLZNotFoundError` | `DIBS_POSTCODE_NOT_FOUND` | `initialize_data` |
| `HkOrUkNotFoundError` | `DIBS_USAGE_TYPE_NOT_FOUND` | `simulator_init` or datasource lookup |
| `UsageTimeError` | `DIBS_USAGE_TIME_NOT_FOUND` | `simulator_init` or datasource lookup |
| `BuildingNotHeatedError` | `DIBS_BUILDING_NOT_HEATED` | `simulate_hours` |
| `UnsupportedSystemError` | `DIBS_UNSUPPORTED_SYSTEM` | `simulate_hours` |
| `SimulationStateError` | `DIBS_INVALID_SIMULATION_STATE` | `simulate_hours` |
| `ThermalCalculationError` | `DIBS_THERMAL_CALCULATION_FAILED` | `simulate_hours` |
| `GHGEmissionError` | `DIBS_GHG_CALCULATION_FAILED` | summary/result calculation |

Host applications should catch `DIBSError` at the integration boundary and use:

- `error.code`
- `error.phase`
- `error.context`
- `str(error)`

Built-in Python errors such as `ValueError` should only be used for programmer errors inside the core. User/data failures should be translated to `DIBSError` subclasses.

## Multiprocessing Notes

`multi()` and `multi_with_batches()` copy the datasource for workers and set `worker_datasource.building` per building.

Datasource implementations should therefore avoid storing non-picklable runtime objects on the datasource instance when using multiprocessing.

Safe patterns:

- immutable configuration values;
- lists of `Building` objects;
- cached lookup tables that can be copied/pickled;
- paths or simple identifiers instead of open file handles.

Risky patterns:

- open file handles;
- database connections stored directly on the datasource object;
- thread locks/process handles;
- request-scoped web objects.

For Django-backed usage, open database work should happen before entering multiprocessing or inside worker-safe methods, not as shared live connection state.

## Regression Commands

Use these commands after changes in the public API, datasource contract, error handling or simulation hot path.

```powershell
python -m pytest -q -p no:cacheprovider tests\error_handling
python -m pytest -q -p no:cacheprovider tests\building_simulator
python scripts\regression_csv_golden.py
```

Expected regression result:

```text
differences=0
```

Optional performance verification:

```powershell
python scripts\profile_building_hotspots.py
```

## Compatibility Rules

- Do not change `DIBS.calculate_result_of_one_building()` return shape without a migration plan.
- Do not change `DIBS.multi()` return shape without a migration plan.
- Do not replace object-based datasource boundaries with dictionaries/DataFrames in the public core API.
- Keep `DataSourceCSV` and `DataSourceDjango` compatible with the same `DataSource` contract.
- Add new datasource requirements here before relying on them in core code.