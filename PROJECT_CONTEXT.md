# PROJECT_CONTEXT.md

## Project Goal

`DibsComputingCore` is the framework-neutral computation engine for DIBS, the
Dynamic ISO Building Simulator. It performs hourly energy simulation for German
non-residential buildings using the simplified ISO 13790:2008 / 5R1C method.

It calculates heating, cooling, hot water, electricity, system energy, primary
energy, greenhouse gas emissions, hourly outputs, and annual summaries.

## Architecture Decisions

- The package is a pure computation library, not an application server.
- Input access is abstracted behind the `DataSource` contract.
- CSV, Django, database, GraphQL, and UI concerns live outside the core.
- Building-hour simulation is stateful; hours inside one building are not
  freely parallelizable.
- Building-level batch execution may use multiprocessing, but error behavior
  must remain explicit and host-compatible.
- Numerical stability and reproducibility take priority over micro-optimizations.

## Directory Structure

```text
src/dibs_computing_core/
  iso_simulator/
    building_simulator/    # simulation orchestration and energy carrier logic
    data_source/           # abstract DataSource contract
    dibs/                  # public DIBS orchestration API
    exceptions/            # typed DIBS errors
    model/                 # Building, result models, thermal helper modules
scripts/                   # regression/profile helper scripts
tests/                     # unit, contract, regression-support tests
docs/                      # error-handling, performance and refactoring plans
```

## Data Flow

```text
Host application / adapter
  -> DataSource implementation
  -> DIBS.calculate_result_of_one_building() or DIBS.multi()
  -> Building simulator and hourly 5R1C loop
  -> hourly results + annual summaries
```

Common adapters:

- `DibsDataSourceCSV`: reads CSV/reference data and produces DIBS inputs.
- `DibsDataSourceDjango`: maps application/database data to DIBS inputs.
- Lezbau: consumes DIBS through its backend workflows.

## Current Project State

Implemented and documented:

- simulator refactoring and enum/readability cleanup;
- building model helper split;
- DIBS error handling contract up to the current completed phase;
- golden regression workflow for the nine-building CSV scenario;
- performance profiling helper scripts.

## Next Milestones

- Keep the current public API stable.
- Run user-led regression checks before any behavioral merge.
- Continue only with clearly scoped new README plans.
- Validate compatibility with both `DibsDataSourceCSV` and `DibsDataSourceDjango`
  before release-oriented changes.

## Known Constraints

- The user executes all tests manually.
- Golden regression must remain `differences=0` for refactors that claim no
  behavioral change.
- Performance claims require measured before/after data.
- Package release steps must not be executed automatically.
