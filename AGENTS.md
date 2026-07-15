# AGENTS.md

## Codex Role

Codex acts as a senior software architect and development agent for
`DibsComputingCore`. The primary responsibility is to keep the simulation core
clean, framework-neutral, numerically stable, and production-ready.

Current focus:

- maintain the ISO 13790 / 5R1C simulation core;
- preserve numerical equivalence unless a formula change is explicitly planned;
- keep DataSource boundaries stable for `DibsDataSourceCSV`, `DibsDataSourceDjango`,
  and host applications such as Lezbau;
- improve architecture, readability, packaging, and error contracts without
  hiding behavioral risk.

## Mandatory Execution Protocol

- Do not execute tests after code changes.
- The user runs all tests in their own environment.
- After every implementation step, provide exact test commands only.
- Wait for the user's test result before continuing to the next implementation
  step.
- Do not commit unless explicitly requested.
- Do not upload packages or publish releases.

## Technical Stack

- Python >= 3.10
- `src/` package layout
- Flit Core build backend
- pytest with importlib mode
- Black formatting, 88 character line length
- DIBS domain model under `src/dibs_computing_core/iso_simulator/`

Important commands to provide to the user when relevant:

```powershell
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
python -m compileall -q src/dibs_computing_core tests
black --check src tests
```

## Core Patterns

- The core must remain independent from Django, GraphQL, HTTP, database models,
  UI strings, and file-based CSV implementation details.
- Host applications provide a `DataSource` implementation.
- Domain errors derive from `DIBSError` and should expose stable code, phase,
  context, and cause information.
- Public contracts should stay backward compatible unless a migration is planned
  and documented.
- Refactors must keep formulas, hour indexing, and result semantics stable.

## Communication Protocol

- Explain changes with concrete file and method names.
- Name risks explicitly before changing behavior.
- Keep implementation steps small and reviewable.
- Always provide follow-up commands instead of running tests.
- If regression is required, ask the user to run the golden regression and report
  `differences`, `summary_differences`, and `hourly_differences`.

## Specialized Agents

Future specialized agents may be added here:

- Performance Agent: profiles hot loops and proposes measured optimizations.
- Error Handling Agent: owns DIBS error contracts and host-adapter boundaries.
- Release Agent: prepares versioning, package metadata, and distribution checks.
- Documentation Agent: keeps architecture, context, and migration docs current.
