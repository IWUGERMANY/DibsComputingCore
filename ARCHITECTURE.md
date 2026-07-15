# ARCHITECTURE.md

## Systemkontext

DIBS ist eine framework-neutrale Python-Bibliothek. Eine Host-Anwendung stellt
Eingaben ueber `DataSource` bereit und verarbeitet die Simulationsergebnisse.

```text
Frontend / API / Batch
  -> Host-Anwendung
  -> konkrete DataSource
  -> DIBS Computing Core
  -> Result / ResultOutput / SummaryResult
```

DIBS kennt keine Django-Modelle, GraphQL-Endpunkte, HTTP-Statuscodes,
Benutzersitzungen oder Frontendtexte.

## Verzeichnisstruktur

```text
DibsComputingCore/
|-- AGENTS.md
|-- CONTEXT.md
|-- ARCHITECTURE.md
|-- pyproject.toml
|-- docs/error_handling/
|-- tests/error_handling/
`-- src/dibs_computing_core/iso_simulator/
    |-- data_source/datasource.py
    |-- dibs/dibs.py
    |-- dibs/dibs_utils/dibs_auxiliary_functions.py
    |-- building_simulator/simulator.py
    |-- model/
    |-- exceptions/
    |-- emission_system.py
    `-- supply_system.py
```

## Kernkomponenten

### DataSource

`data_source/datasource.py` ist die Integrationsgrenze. Host-Anwendungen
liefern darueber `Building`, Wetterstunden, EPW-Metadaten, Profile,
Nutzungszeiten, Gewinne sowie Energie- und Emissionsfaktoren. Der Core greift
nicht direkt auf Datenbanken oder Dateien zu.

### DIBS

`dibs/dibs.py` orchestriert Dateninitialisierung, Simulatoraufbau,
Stundenberechnung, Summary-Aufbau und Fehlerweitergabe. Der zentrale
Einzelgebaeude-Einstieg ist:

```python
DIBS.calculate_result_of_one_building()
```

### BuildingSimulator

`building_simulator/simulator.py` verbindet Gebaeude, Wetter, Fenster,
Nutzungsprofile, interne Gewinne, Versorgungssysteme und Emissionsfaktoren.
Beim Aufbau werden Fenster, Wetterdaten und Sonnenpositionen vorbereitet.

### Stunden-Orchestrierung

`extracted_method_to_simulate_one_building()` fuehrt 8760 Zeitschritte aus:

```text
Wetter
  -> Sonnenstand und Fenstergewinne
  -> Nutzung und interne Gewinne
  -> thermischer Heiz-/Kuehlbedarf
  -> Warmwasser und Systemenergie
  -> Stundenergebnis
```

Die Stunden eines Gebaeudes sind durch den thermischen Folgezustand seriell
voneinander abhaengig.

### Thermischer Kern

`model/building.py` enthaelt die 5R1C- und Crank-Nicolson-Berechnung,
Lueftungs- und Waermeuebergangsverluste, Heiz-/Kuehlbedarf und
Leistungsbegrenzungen. Optional kann Numba den thermischen Hotpath ausfuehren.

### Emissions- und Versorgungssysteme

`emission_system.py` modelliert die Raumuebergabe. `supply_system.py` wandelt
thermische Lasten in Strom- und Brennstoffbedarf um.

### Ergebnisobjekte

- `Result`: stuendliche Reihen.
- `ResultOutput`: aggregierte Energie-, System- und Emissionswerte.
- `SummaryResult`: kompakte Jahres- und Kennwerte.

## Datenfluss eines Einzelgebaeudes

```text
1. Host erstellt DataSource
2. DIBS liest Steuerungswerte
3. initialize_data()
   |-- get_user_building()
   |-- get_epw_pe_factors()
   `-- get_epw_file()
4. BuildingSimulator wird aufgebaut
5. Gebaeude wird validiert
6. 8760 Stunden werden seriell simuliert
7. ResultOutput aggregiert Stundenwerte
8. SummaryResult wird erzeugt
9. Ergebnisse gehen an den Host
```

## Fehlerfluss

Erwartete Fehler erben von `DIBSError`:

```text
DIBSError
|-- DIBSInputError
|-- DIBSDataSourceError
|-- DIBSConfigurationError
|-- DIBSSimulationError
`-- DIBSResultError
```

Fehler koennen `code`, `phase`, `context` und `message` enthalten. Die
Einzelgebaeude-Grenze verwendet die Phasen `initialize_data`,
`simulator_init`, `simulate_hours` und `summary_wrap`. Der Host uebernimmt
finales Logging und API-Mapping.

## Gebaeudebestand und Parallelisierung

`multi()` und `multi_with_batches()` parallelisieren verschiedene Gebaeude mit
`multiprocessing.Pool`. Die Stunden innerhalb eines Gebaeudes bleiben seriell.
Der Batch-Fehler- und Partial-Result-Vertrag ist noch offen.

## Abhaengigkeitsrichtung

```text
Host
  -> DataSource
  -> DIBS
  -> BuildingSimulator / Stunden-Orchestrierung
  -> Building / Window / Systeme
  -> Ergebnisobjekte
```

Eine Abhaengigkeit `Core -> Django/GraphQL/Datenbank` ist nicht erlaubt.

## Standardplatz fuer neue Features

| Feature | Zielort |
|---|---|
| neue Datenquelle | Host-Projekt als `DataSource`-Implementierung |
| neue Orchestrierungsphase | `dibs/dibs.py` |
| neue Stundenlogik | `dibs_utils/dibs_auxiliary_functions.py` |
| neue Gebaeude-/Thermikformel | `model/building.py` |
| neues Fenstermodell | `model/window.py` |
| neues Versorgungssystem | `supply_system.py` |
| neues Emissionssystem | `emission_system.py` |
| neues Domain-/Ergebnisobjekt | `model/` |
| neue erwartete Fehlerart | `exceptions/` plus zentraler Export |
| Regressionstest | `tests/` im passenden Fachbereich |

Ein neues Ergebnisfeld muss vom Berechnungsort ueber Stundenresultat,
Aggregation und Summary bis zum Host durchgaengig erweitert werden.

## Performance-Pfade

```text
DIBS_USE_PREALLOC_RESULTS=1
LBBD_ENABLE_NUMBA_THERMAL=1
```

`SIM_PERF` ist temporaere Messinstrumentierung und keine fachliche Komponente.

## Offene Architekturpunkte

- Batch-/Multiprocessing-Fehler und Partial Results.
- Eigenstaendige Golden-Snapshot-Regression.
- Explizite Public API im obersten Package-`__init__.py`.
- Deklarierte Dev- und optionale Abhaengigkeiten.
- Spaetere Entfernung von `SIM_PERF`.

## Dokumentabgrenzung

| Dokument | Zweck |
|---|---|
| `README.md` | Projekteinstieg |
| `CONTEXT.md` | kurzer fachlicher und technischer Kontext |
| `ARCHITECTURE.md` | Komponenten, Datenfluss und Feature-Platzierung |
| `AGENTS.md` | Arbeitsregeln, Befehle und Qualitaetsanforderungen |
