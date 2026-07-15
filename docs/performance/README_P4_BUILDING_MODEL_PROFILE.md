# P4 Building Model Profiling

## Ziel

P4 analysiert `src/dibs_computing_core/iso_simulator/model/building.py`, ohne
Formeln oder Ergebnislogik zu aendern. Der Zweck ist, konkrete Hotloop-Kandidaten
zu finden, bevor P5 Optimierungen am thermischen Kern erlaubt.

## Relevante Laufzeitkette

```text
DIBS.multi()
  -> calculate_result_of_all_buildings()
  -> calculate_result_of_one_building()
  -> extracted_method_to_simulate_one_building()
  -> pro Stunde:
       Building.calc_h_ve_adj()
       Building.solve_building_lighting()
       Building.solve_building_energy()
         -> Building.has_demand()
            -> Building.calc_temperatures_crank_nicolson()
               -> Building.calc_heat_flow()
         -> Building.calc_energy_demand() falls Heating/Cooling aktiv
            -> Building.calc_temperatures_crank_nicolson() mehrfach
            -> SupplyDirector + SupplySystem
```

## Statische Findings

| Prioritaet | Datei/Funktion | Finding | Warum relevant | Risiko |
|---|---|---|---|---|
| P4-F1 | `building.py::calc_temperatures_crank_nicolson` | Der thermische Kern wird pro Stunde mindestens einmal und bei Demand mehrfach aufgerufen. | Sehr wahrscheinlich CPU-relevant, aber fachlich sensibel. | Hoch |
| P4-F2 | `building.py::calc_heat_flow` | Pro Temperaturberechnung werden `EmissionDirector` und Emission-Systemobjekte erzeugt. | Objektallokation im Hotloop kann messbar sein. | Mittel bis hoch |
| P4-F3 | `building.py::solve_building_energy` | `SupplyDirector()` wird bei jeder Stunde mit Heating/Cooling Demand neu erzeugt. | Demand-Stunden erzeugen zusaetzliche Objekte. | Mittel |
| P4-F4 | `building.py::calc_h_ve_adj` | Mehrfach verschachtelte Branches berechnen wiederholt konstante Ventilationsfaktoren. | Pro Stunde ausgefuehrt, Konstanten koennten vorbereitet werden. | Mittel |
| P4-F5 | `building.py::solve_building_lighting` | `lighting_load * net_room_area` und weitere Faktoren sind gebaeudekonstant. | Pro Stunde klein, aber sicher vorberechenbar. | Niedrig |
| P4-F6 | `building.py::has_demand` und `calc_energy_demand` | `calc_temperatures_crank_nicolson()` wird fuer 0 W, 10 W/m2 und final demand wiederholt. | Fachlich notwendig nach ISO-Verfahren, aber nur profiler-basiert anfassen. | Hoch |

## Profiling-Skript

Neu:

```text
scripts/profile_building_hotspots.py
```

Das Skript instrumentiert ausgewaehlte `Building`-Methoden zur Laufzeit und
fuehrt den gleichen 9-Gebaeude-CSV-Pfad aus wie die Golden Regression.

Wichtig: Fuer die Messung wird bewusst eine sequentielle All-Buildings-Schleife
im Parent-Prozess benutzt. `DIBS.multi()` nutzt `multiprocessing.Pool`; dort
wuerden die Monkeypatch-Zaehler im Parent-Prozess bei `calls=0` bleiben, obwohl
die Simulation in Child-Prozessen laeuft. Der Produktivpfad bleibt unveraendert.

Ausfuehren aus dem Root von `DibsComputingCore`:

```powershell
python scripts\profile_building_hotspots.py
```

Output:

```text
performance_results/building_hotspot_profile.csv
```

Die CSV enthaelt:

- `method`
- `calls`
- `total_s`
- `avg_us`
- `max_us`
- `share_of_profiled_time`

## Aktuelle Profiling-Messung

Ausgefuehrt mit:

```powershell
python scripts\profile_building_hotspots.py
```

Ergebnis fuer 9 Gebaeude:

```text
buildings=9
simulation_time_s=19.228410 wall_time_s=19.228620
```

Hinweis: Diese Laufzeit ist nicht mit `DIBS.multi()` vergleichbar, weil das
Skript sequentiell misst und jede profilierte Methode per Wrapper zaehlt. Die
Tabelle ist fuer Hotspot-Ranking gedacht, nicht fuer End-to-End-Performance.

| Rang | Methode | Calls | total_s | Anteil |
|---:|---|---:|---:|---:|
| 1 | `solve_building_energy` | 78840 | 4.701147 | 33.73% |
| 2 | `calc_temperatures_crank_nicolson` | 294624 | 3.053178 | 21.91% |
| 3 | `calc_energy_demand` | 71928 | 2.580314 | 18.51% |
| 4 | `has_demand` | 78840 | 1.634598 | 11.73% |
| 5 | `calc_heat_flow` | 294624 | 1.337965 | 9.60% |
| 6 | `calc_h_ve_adj` | 78840 | 0.314387 | 2.26% |
| 7 | `solve_building_lighting` | 78840 | 0.129502 | 0.93% |
| 8 | `calc_energy_demand_unrestricted` | 71928 | 0.095762 | 0.69% |
| 9 | `check_night_flushing` | 78840 | 0.090562 | 0.65% |

Interpretation: Der staerkste Hebel liegt nicht bei kleinen Hilfsfunktionen,
sondern im Energiepfad: `solve_building_energy`, Demand-Ermittlung und
Crank-Nicolson-Temperaturrechnung. Optimierungen an `calc_h_ve_adj` oder
Lighting sind wahrscheinlich kleiner.
## P5-Nachmessung

Nach P5 wurden `EmissionDirector`, `SupplyDirector` und die konkreten Systemklassen pro `Building` vorbereitet. Die thermischen Formeln wurden nicht geaendert.

Regression:

```text
differences=0
```

Profiling nach P5 fuer 9 Gebaeude:

```text
buildings=9
simulation_time_s=22.066454 wall_time_s=22.066827
```

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

Bewertung: P5 ist stabil, aber die dominante Hotspot-Struktur bleibt gleich. Weitere groessere Optimierungen sollten nach dem geplanten `building.py`-Split erfolgen.
## Bewertung nach Messung

P5 darf erst gestartet werden, wenn das Profiling zeigt, dass eine Funktion
messbar relevant ist. Ohne klare Messung sollten keine thermischen Formeln
veraendert werden.

## Empfohlene naechste P5-Kandidaten

1. Nur wenn `calc_heat_flow()` viel Zeit verbraucht: EmissionDirector- und
   Emission-System-Allokation reduzieren.
2. Nur wenn `calc_h_ve_adj()` sichtbar ist: gebaeudekonstante Ventilationswerte
   vorberechnen.
3. Nur wenn `solve_building_lighting()` sichtbar ist: Lighting-Konstanten im
   Konstruktor vorberechnen.
4. `calc_temperatures_crank_nicolson()` nur anfassen, wenn Profiling klar zeigt,
   dass es dominiert und Golden Regression danach `differences=0` bleibt.

## Verbindliche Validierung nach jeder Optimierung

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```
