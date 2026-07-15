# DIBS Core: Naechste Optimierungs-Prioritaeten

## Ziel

Diese Datei beschreibt die sinnvollsten naechsten Optimierungsschritte fuer
`DibsComputingCore` nach Abschluss von:

- Simulator-Refactoring `P1` bis `P12`
- Error-Handling-Migration `D-EH1` bis `D-EH10`
- Golden Regression mit `differences=0`

Wichtig: Ab jetzt sollten nur noch messbare, kleine Schritte umgesetzt werden.
Jede Optimierung muss die Golden Regression bestehen.

## Verbindliche Pruefung nach jeder Optimierung

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P1: Performance-Logging schaltbar machen

### Problem

`SIM_PERF`-Logs waren fuer Analyse und Optimierung hilfreich. Langfristig sollen
sie aber nicht permanent in Host-Anwendungen wie Lezbau oder Batch-Laeufen
auftauchen.

### Vorschlag

Performance-Logs ueber ein Environment-Flag steuern:

```text
DIBS_PERF_LOG=1
```

Nur wenn dieses Flag aktiv ist, werden `SIM_PERF`-Logs geschrieben.

### Erwarteter Effekt

- sauberere Logs;
- weniger I/O;
- bessere Integration in Lezbau;
- keine fachliche Ergebnisveraenderung.

### Risiko

Niedrig. Es darf nur Logging betreffen, nicht den Simulationsablauf.

### Prioritaet

Hoch.

### Status

Umgesetzt. `SIM_PERF`-Logs werden nur noch geschrieben, wenn `DIBS_PERF_LOG` auf einen der folgenden Werte gesetzt ist:

```text
1, true, yes, on
```

Ohne Flag bleibt der Rueckgabewert `simulation_time` unveraendert, aber die zusaetzlichen Performance-Logs werden unterdrueckt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/dibs/dibs.py`
- `docs/performance/README_DIBS_CORE_NEXT_OPTIMIZATION_PRIORITIES.md`

## P2: Golden Regression um Stundenwerte erweitern

### Problem

Die aktuelle Golden Regression prueft Summary-Ergebnisse fuer 9 Gebaeude. Das
ist stark, aber Hotloop-Aenderungen koennen theoretisch einzelne Stundenwerte
veraendern, ohne sofort in jeder Summary sichtbar zu werden.

### Vorschlag

Zusatzvergleich fuer ausgewaehlte Stundenwerte einfuehren, zum Beispiel fuer 1
bis 2 Gebaeude:

- `heating_demand`
- `cooling_demand`
- `hot_water_demand`
- `t_air`
- `solar_gains_total`
- `lighting_demand`

### Erwarteter Effekt

- bessere Absicherung bei Hotloop-Optimierungen;
- besserer Schutz fuer `WindowCalculator`, `HotWaterCalculator` und
  `Building.solve_building_energy`;
- schnellere Ursachenanalyse bei Regressionen.

### Risiko

Mittel. Die Vergleichsdateien duerfen nicht zu gross oder schwer wartbar werden.

### Prioritaet

Hoch.

### Status

Umgesetzt. `scripts/regression_csv_golden.py` erzeugt und vergleicht jetzt neben der Summary-Golden-Datei auch eine kompakte Stundenwert-Golden-Datei:

```text
tests/golden/hourly_sample_9_buildings.csv
```

Verglichen werden ausgewaehlte Stunden und Hotloop-Felder wie Heating/Cooling Demand, Hot-Water Demand, Air Temperature, Lighting Demand, Internal Gains und Solar Gains. Die Excel-Ausgabe enthaelt zusaetzlich `HourlyCurrent` und `HourlyDiff`.

Geaendert:

- `scripts/regression_csv_golden.py`
- `scripts/README_GOLDEN_REGRESSION.md`
- `docs/performance/README_DIBS_CORE_NEXT_OPTIMIZATION_PRIORITIES.md`

## P3: DataSourceCSV separat optimieren

### Problem

Ein Teil der Laufzeit und Fehleranfaelligkeit liegt nicht im Core, sondern im
CSV-Adapter. Der Core soll DataSource-neutral bleiben.

### Vorschlag

Im Package `DibsDataSourceCSV` separat pruefen:

- statische Tabellen pro Prozess nur einmal laden;
- Input-Spalten frueh validieren;
- CSV-/Excel-Lesefehler in DIBS-kompatible Exceptions uebersetzen;
- wiederholtes Parsing vermeiden;
- gleiche Inputs fuer `calculate_result_of_one_building()` und `multi()`
  konsistent bereitstellen.

### Erwarteter Effekt

- bessere Cold-Start-Zeit;
- stabilere Fehlermeldungen;
- weniger I/O;
- bessere Kompatibilitaet mit Error Handling.

### Risiko

Mittel. DataSourceCSV darf weiterhin den Core-Vertrag erfuellen und muss mit
`SimulationData_Breitenerhebung.csv` identische Ergebnisse liefern.

### Prioritaet

Hoch.

### Status

Umgesetzt bzw. bewusst in das separate Package `DibsDataSourceCSV` ausgelagert.
Der Core bleibt DataSource-neutral; die CSV-spezifischen Optimierungen wurden nicht in `DibsComputingCore` gezogen.

Dokumentation und Umsetzung liegen in:

```text
C:\Users\wail\Desktop\Projects\Stand dibs\DibsDataSourceCSV\README_OPTIMIZATION_PLAN.md
C:\Users\wail\Desktop\Projects\Stand dibs\DibsDataSourceCSV\README_DATASOURCE_SPLIT_PLAN.md
C:\Users\wail\Desktop\Projects\Stand dibs\DibsDataSourceCSV\scripts\README_GOLDEN_REGRESSION.md
```

Umgesetzt bzw. vorbereitet wurden dort:

- CSV-/Excel-Lesefehler werden in DIBS-kompatible Exceptions uebersetzt.
- Building-Spalten werden explizit validiert und per Namen statt fragiler Reihenfolge gemappt.
- EPW-, Schedule- und Weather-Daten nutzen separate, testbare Cache-Pfade.
- CSV-Leselogik wurde zentralisiert, damit Fehlerbehandlung und Optionen konsistent bleiben.
- `DataSourceCSV` wurde modular aufgeteilt, ohne die oeffentliche `DataSourceCSV`-API zu brechen.
- Golden Regression fuer das 9-Gebaeude-Szenario bleibt der verbindliche Nachweis fuer Ergebnisgleichheit.

Verbindliche Pruefung in `DibsDataSourceCSV`:

```powershell
python -m pytest -q -p no:cacheprovider
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P4: `Building`-Modell gezielt profilieren

### Problem

`model/building.py` enthaelt den thermischen Kern. Dort liegt wahrscheinlich ein
Teil der CPU-Zeit, aber das fachliche Risiko ist hoch.

### Vorschlag

Erst messen, dann optimieren:

- Welche Properties werden pro Stunde mehrfach berechnet?
- Welche Werte sind konstant pro Gebaeude?
- Welche Formeln koennen sicher vorbereitet werden?
- Wo entstehen unnoetige Attributzugriffe?

### Erwarteter Effekt

- potenziell bessere Laufzeit im Hotloop;
- weniger CPU-Arbeit pro Stunde;
- klarere Trennung zwischen Gebaeude-Konstanten und Stundenwerten.

### Risiko

Hoch. Kleine Formel- oder Reihenfolgeaenderungen koennen Ergebnisse veraendern.

### Prioritaet

Mittel.

### Status

Analyse- und Profiling-Schritt vorbereitet. Details stehen in:

```text
docs/performance/README_P4_BUILDING_MODEL_PROFILE.md
scripts/profile_building_hotspots.py
```

P4 aendert keine Simulationsformeln. Das Profiling-Skript misst Building-Hotspot-Methoden im 9-Gebaeude-CSV-Szenario und schreibt `performance_results/building_hotspot_profile.csv`. P5 soll nur auf Basis dieser Messung gestartet werden.

## P5: Hotloop nur noch profiler-basiert optimieren

### Problem

Nach den bisherigen Optimierungen ist blindes Refactoring riskant. Weitere
Hotloop-Aenderungen sollen nur erfolgen, wenn Messungen einen klaren Engpass
zeigen.

### Kandidaten

- `Window.calc_solar_gains_precomputed()`
- `Window.calc_illuminance_precomputed()`
- `Building.solve_building_energy()`
- `calc_temperatures_crank_nicolson()`
- Ergebnislisten und Result-Objekte

### Erwarteter Effekt

- gezielte Laufzeitverbesserung;
- weniger Risiko durch kleine, messbare Schritte.

### Risiko

Mittel bis hoch, je nach Funktion.

### Prioritaet

Mittel.

### Status

P5-Start umgesetzt in `src/dibs_computing_core/iso_simulator/model/building.py`.

Aenderung:

- `EmissionDirector()` wird nicht mehr in jedem `calc_heat_flow()`-Call neu erzeugt, sondern einmal pro `Building` vorbereitet.
- `SupplyDirector()` wird nicht mehr in jedem Demand-Call von `solve_building_energy()` neu erzeugt, sondern einmal pro `Building` vorbereitet.
- Die konkreten Heating-/Cooling-Emission- und Supply-Klassen werden im Konstruktor einmal aus den Mapping-Dicts gelesen und im Hotloop direkt verwendet.

Warum:

- P4-Profiling zeigte `solve_building_energy`, `calc_temperatures_crank_nicolson`, `calc_energy_demand`, `has_demand` und `calc_heat_flow` als dominante Hotspots.
- Diese P5-Aenderung reduziert Objekt-Allokationen und Dict-Lookups im Hotloop, ohne thermische Formeln oder Ergebnislogik zu aendern.

Erwartete Pruefung durch den Nutzer:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
python scripts\profile_building_hotspots.py
```

Erwartung fuer Regression:

```text
differences=0
```

### P5-Abschlussmessung

Vom Nutzer geprueft:

```text
differences=0
buildings=9
simulation_time_s=22.066454 wall_time_s=22.066827
```

Profiling nach P5:

| Rang | Methode | Calls | total_s | Anteil |
|---:|---|---:|---:|---:|
| 1 | `solve_building_energy` | 78840 | 7.538812 | 34.03% |
| 2 | `calc_temperatures_crank_nicolson` | 294624 | 4.804266 | 21.68% |
| 3 | `calc_energy_demand` | 71928 | 4.071863 | 18.38% |
| 4 | `has_demand` | 78840 | 2.681384 | 12.10% |
| 5 | `calc_heat_flow` | 294624 | 2.059672 | 9.30% |
| 6 | `calc_h_ve_adj` | 78840 | 0.486894 | 2.20% |
| 7 | `solve_building_lighting` | 78840 | 0.217393 | 0.98% |
| 8 | `calc_energy_demand_unrestricted` | 71928 | 0.149903 | 0.68% |
| 9 | `check_night_flushing` | 78840 | 0.145784 | 0.66% |

Bewertung:

- P5 ist fachlich stabil, weil die Golden Regression `differences=0` liefert.
- Die Hotspot-Reihenfolge bleibt unveraendert.
- Weitere Optimierungen im Energy-Pfad sollten erst nach dem geplanten `building.py`-Split erfolgen, damit Performance-Logik und Strukturarbeit nicht vermischt werden.

Naechster Block:

```text
docs/performance/README_BUILDING_MODEL_SPLIT_PLAN.md
```

## P6: Public API und DataSource-Vertrag dokumentieren

### Problem

Der Core wird von mehreren Host-Schichten verwendet: `DataSourceCSV`,
`DataSourceDjango` und Lezbau. Der Vertrag sollte explizit dokumentiert sein.

### Vorschlag

Eine API-/Integration-Doku ergaenzen fuer:

- `DIBS.calculate_result_of_one_building()`
- `DIBS.multi()`
- erwartete DataSource-Attribute;
- erwartete DataSource-Methoden;
- erwartete Exceptions;
- Regression-Test-Befehl.

### Erwarteter Effekt

- einfachere Integration in Lezbau;
- weniger Missverstaendnisse beim Error Handling;
- bessere Wartbarkeit bei weiteren DataSources.

### Risiko

Niedrig. Dokumentationsschritt.

### Prioritaet

Mittel.

### Status

Umgesetzt als Dokumentationsschritt.

Neue Vertragsdoku:

```text
docs/integration/README_PUBLIC_API_DATASOURCE_CONTRACT.md
```

Dokumentiert wurden:

- stabile `DIBS`-Entry-Points;
- Rueckgabeformen von `calculate_result_of_one_building()`, `multi()` und `multi_with_batches()`;
- erwartete `DataSource`-Methoden;
- erforderliche DataSource-State-Attribute;
- erwartete Core-Modellobjekte;
- DIBS-Error-Contract mit `DIBSError`, `code`, `phase` und `context`;
- Multiprocessing-Hinweise fuer DataSourceCSV/DataSourceDjango;
- Regression-Test-Befehle.

## Empfohlene Reihenfolge

```text
P1  Performance-Logging schaltbar machen
P2  Golden Regression um Stundenwerte erweitern
P3  DataSourceCSV separat optimieren
P4  Building-Modell gezielt profilieren
P5  Hotloop nur profiler-basiert optimieren
P6  Public API und DataSource-Vertrag dokumentieren
```

## Nicht-Ziele

Diese Optimierungsphase soll nicht:

- neue Fachformeln einfuehren;
- DataSourceCSV oder DataSourceDjango in den Core ziehen;
- gueltige Golden-Ergebnisse veraendern;
- weitere grosse Refactorings ohne Messgrundlage starten;
- Django-, GraphQL- oder Lezbau-Abhaengigkeiten in DibsComputingCore einfuehren.