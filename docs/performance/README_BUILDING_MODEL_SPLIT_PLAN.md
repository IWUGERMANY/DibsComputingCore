# Building Model Split Plan

## Ziel

`src/dibs_computing_core/iso_simulator/model/building.py` enthaelt aktuell mehrere Verantwortlichkeiten in einer Datei:

- Gebaeude-Datenmodell und Konstanten
- Ventilation und Night-Flushing
- Lighting Demand
- thermischer Crank-Nicolson-Kern
- Heat-Flow/Emission-Systeme
- Heating-/Cooling-Demand und Supply-Systeme

Der Split soll die Datei kleiner und wartbarer machen, ohne fachliche Formeln oder Simulationsergebnisse zu veraendern.

Wichtig: Dieser Schritt ist primaer Architektur/Readability. Laufzeitgewinne sind nur indirekt zu erwarten, weil spaetere Hotloop-Optimierungen sicherer und gezielter werden.

## Regeln fuer den Split

- Keine Formel aendern.
- Keine Reihenfolge im Stundenloop aendern.
- Public API von `Building` stabil halten.
- Bestehende Methoden duerfen zunaechst als Methoden auf `Building` bleiben und intern delegieren.
- Nach jedem Schritt Golden Regression ausfuehren.
- Wenn `differences != 0`, Schritt stoppen und Ursache klaeren.

## Validierung nach jedem Schritt

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
python scripts\profile_building_hotspots.py
```

Erwartung:

```text
differences=0
```

## B-S1: Thermal Core auslagern

### Ziel

Die reinen Crank-Nicolson-Hilfsfunktionen aus `building.py` in ein separates Modul verschieben.

### Neue Datei

```text
src/dibs_computing_core/iso_simulator/model/thermal_core.py
```

### Verschieben

- `_thermal_core_py`
- `_thermal_core_numba`
- optionaler `numba`-Import

### Warum zuerst?

Dieser Teil ist bereits fast eigenstaendig und hat eine klare Eingabe/Rueckgabe-Struktur. Das Risiko ist geringer als bei `solve_building_energy()`.

### Risiko

Niedrig bis mittel. Wichtig ist, dass Numba-Cache und Fallback-Verhalten gleich bleiben.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/thermal_core.py` neu erstellt.
- `_thermal_core_py` und `_thermal_core_numba` aus `building.py` ausgelagert.
- `building.py` importiert `_thermal_core_numba` aus `.thermal_core`.
- Keine Formel und keine Aufrufreihenfolge geaendert.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; files=[r'src\dibs_computing_core\iso_simulator\model\building.py', r'src\dibs_computing_core\iso_simulator\model\thermal_core.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S2: Energy Demand in eigenes Modul vorbereiten

### Ziel

Die Energy-Pfad-Methoden aus `Building` fachlich gruppieren.

### Kandidaten

- `solve_building_energy()`
- `has_demand()`
- `calc_energy_demand()`
- `calc_energy_demand_unrestricted()`

### Moeglicher Pfad

```text
src/dibs_computing_core/iso_simulator/model/building_energy.py
```

### Umsetzung

Erst nur Hilfsfunktionen extrahieren oder Delegation einfuehren. Die public Methoden auf `Building` bleiben zunaechst erhalten.

### Risiko

Mittel bis hoch. Dieser Pfad dominiert laut P4/P5-Profiling die Laufzeit und ist fachlich sensibel.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_energy.py` neu erstellt.
- `solve_building_energy()` ausgelagert.
- `has_demand()` ausgelagert.
- `calc_energy_demand()` ausgelagert.
- `calc_energy_demand_unrestricted()` ausgelagert.
- `Building` behaelt alle public Methoden als duenne Wrapper, damit externe Aufrufe, Tests und Profiling-Methodennamen stabil bleiben.

Nicht geaendert:

- keine thermische Formel;
- keine Reihenfolge der Demand-Ermittlung;
- keine Public API von `Building`;
- keine Ergebnisstruktur.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; files=[r'src\dibs_computing_core\iso_simulator\model\building.py', r'src\dibs_computing_core\iso_simulator\model\building_energy.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S3: Heat Flow / Emission auslagern

### Ziel

`calc_heat_flow()` und die Emission-System-Anbindung aus `building.py` herausloesen.

### Neuer Pfad

```text
src/dibs_computing_core/iso_simulator/model/building_heat_flow.py
```

### Inhalt

- Heat-Flow-Verteilung auf `phi_ia`, `phi_st`, `phi_m`
- Auswahl Heating-/Cooling-Emission-Klasse
- Verwendung des vorbereiteten `EmissionDirector`

### Risiko

Mittel. Die Funktion wird sehr oft aufgerufen und beeinflusst alle thermischen Ergebnisse.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_heat_flow.py` neu erstellt.
- `calc_heat_flow()` ausgelagert.
- `Building.calc_heat_flow()` bleibt als duenner Wrapper erhalten, damit externe Aufrufe und Profiling stabil bleiben.

Nicht geaendert:

- keine Heat-Flow-Formel;
- keine Emission-System-Auswahl;
- keine Mutation der Building-Zustandsfelder;
- keine Public API von `Building`.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; files=[r'src\dibs_computing_core\iso_simulator\model\building.py', r'src\dibs_computing_core\iso_simulator\model\building_heat_flow.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S4: Ventilation auslagern

### Ziel

Ventilation und Night-Flushing isolieren.

### Neuer Pfad

```text
src/dibs_computing_core/iso_simulator/model/building_ventilation.py
```

### Kandidaten

- `calc_h_ve_adj()`
- `check_night_flushing()`

### Warum sinnvoll?

Diese Logik ist fachlich abgegrenzt und pro Stunde aktiv. Sie ist nicht der groesste Hotspot, aber die aktuelle Methode ist verzweigt und schwer zu lesen.

### Risiko

Mittel. Night-Flushing aendert `t_set_heating`, deshalb Reihenfolge und Seiteneffekte exakt beibehalten.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_ventilation.py` neu erstellt.
- `calc_h_ve_adj()` ausgelagert.
- `check_night_flushing()` ausgelagert.
- `Building.calc_h_ve_adj()` und `Building.check_night_flushing()` bleiben als duenne Wrapper erhalten.

Nicht geaendert:

- keine Ventilationsformel;
- keine Night-Flushing-Bedingung;
- der Seiteneffekt `t_set_heating = 0` bleibt an denselben fachlichen Stellen;
- keine Public API von `Building`.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; files=[r'src\dibs_computing_core\iso_simulator\model\building.py', r'src\dibs_computing_core\iso_simulator\model\building_ventilation.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S4b: Ventilation vereinfachen

### Ziel

`calc_h_ve_adj()` war nach B-S4 fachlich isoliert, aber noch stark verschachtelt. B-S4b reduziert die Verzweigungen, ohne die Ventilationsformeln oder Seiteneffekte zu aendern.

### Umsetzung

Neue interne Hilfsfunktionen in `building_ventilation.py`:

- `_is_usage_time(daytime, usage_start, usage_end)` fuer normale und uebernachtende Nutzungsfenster.
- `_infiltration_h_ve(building)` fuer reine Infiltration.
- `_usage_h_ve(building)` fuer Ventilation waehrend Nutzungszeit.
- `_night_flushing_h_ve(building)` fuer Night-Flushing.

Neue Entscheidungsreihenfolge:

1. Wenn `ach_vent == 0` und `ach_win == 0`: reine Infiltration wie vorher.
2. Wenn `night_flushing_on`: Night-Flushing-Wert setzen und `t_set_heating = 0` wie vorher.
3. Wenn Nutzungszeit: Nutzungszeit-Ventilation wie vorher.
4. Sonst: reine Infiltration wie vorher.

### Status

Umgesetzt.

Nicht geaendert:

- keine Ventilationsformel;
- keine Night-Flushing-Bedingung;
- `t_set_heating = 0` bleibt im Night-Flushing-Pfad;
- keine Public API von `Building`.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; ast.parse(pathlib.Path(r'src\dibs_computing_core\iso_simulator\model\building_ventilation.py').read_text(encoding='utf-8')); print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```
## B-S5: Lighting auslagern

### Ziel

Lighting Demand getrennt halten.

### Neuer Pfad

```text
src/dibs_computing_core/iso_simulator/model/building_lighting.py
```

### Kandidat

- `solve_building_lighting()`

### Risiko

Niedrig. Die Methode ist klein und fachlich gut isoliert.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_lighting.py` neu erstellt.
- `solve_building_lighting()` ausgelagert.
- `Building.solve_building_lighting()` bleibt als duenner Wrapper erhalten, damit externe Aufrufe und Profiling stabil bleiben.

Nicht geaendert:

- keine Lighting-Formel;
- keine Lux-Grenzbedingung;
- keine Mutation von `lighting_demand`;
- keine Public API von `Building`.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; files=[r'src\dibs_computing_core\iso_simulator\model\building.py', r'src\dibs_computing_core\iso_simulator\model\building_lighting.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S6: Building als Orchestrator stabilisieren

### Ziel

Nach den Auslagerungen bleibt `Building` die zentrale Objekt-API, aber nicht mehr die Datei mit allen Details.

### Erwartete Struktur

`Building` enthaelt weiterhin:

- Konstruktor und Gebaeude-Konstanten
- Zustand der aktuellen Stunde
- public Methoden als stabile API
- Delegation an kleinere Module

### Nicht-Ziel

Kein kompletter Umbau auf viele neue Klassen in einem Schritt. Erst kleine Module, dann optional spaeter bessere Objektgrenzen.

### Status

Umgesetzt.

Geaendert:

- `building.py` enthaelt jetzt einen klar markierten Delegationsabschnitt fuer die stabilen public Methoden.
- Der nach den Auslagerungen ungenutzte direkte Exception-Import wurde aus `building.py` entfernt.
- `Building` bleibt zentrale Objekt-API und delegiert an:
  - `building_ventilation.py`
  - `building_lighting.py`
  - `building_energy.py`
  - `building_heat_flow.py`
  - `thermal_core.py`

Nicht geaendert:

- keine Public API von `Building`;
- keine Simulationsformel;
- keine Ergebnisstruktur;
- kein Umbau auf neue Klassen.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; ast.parse(pathlib.Path(r'src\dibs_computing_core\iso_simulator\model\building.py').read_text(encoding='utf-8')); print('syntax ok')"
```

Noch vom Nutzer zu pruefen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## B-S7: Nach Split erneut P5/P6 bewerten

### Ziel

Nach dem Split erneut messen:

```powershell
python scripts\profile_building_hotspots.py
```

Dann entscheiden, ob weitere Performance-Arbeit sinnvoll ist.

### Status

Umgesetzt und bewertet.

Profiling nach Split und B-S4b, ausgefuehrt mit angeschlossenem Laptop:

```text
buildings=9
simulation_time_s=12.923055 wall_time_s=12.923273
```

| Rang | Methode | Calls | total_s | Anteil |
|---:|---|---:|---:|---:|
| 1 | `solve_building_energy` | 78840 | 4.848111 | 33.86% |
| 2 | `calc_temperatures_crank_nicolson` | 294624 | 3.103735 | 21.67% |
| 3 | `calc_energy_demand` | 71928 | 2.629206 | 18.36% |
| 4 | `has_demand` | 78840 | 1.711780 | 11.95% |
| 5 | `calc_heat_flow` | 294624 | 1.331914 | 9.30% |
| 6 | `calc_h_ve_adj` | 78840 | 0.345970 | 2.42% |
| 7 | `solve_building_lighting` | 78840 | 0.141347 | 0.99% |
| 8 | `calc_energy_demand_unrestricted` | 71928 | 0.104841 | 0.73% |
| 9 | `check_night_flushing` | 78840 | 0.102804 | 0.72% |

### Bewertung

- Der Split verbessert Architektur und Lesbarkeit, ist aber kein grosser Performance-Hebel.
- Die absolute Laufzeit ist mit angeschlossenem Laptop deutlich niedriger als im Akku-Modus; deshalb sind Prozentanteile wichtiger als Einzelzeiten.
- Die Hotspot-Reihenfolge bleibt stabil: Der dominante Pfad ist weiterhin `solve_building_energy()` mit Demand-Ermittlung und Crank-Nicolson-Temperaturrechnung.
- `calc_h_ve_adj()` und `solve_building_lighting()` sind nach dem Split klarer isoliert, aber bleiben kleine Hotspots.

### Naechste Optionen

1. Performance: Arbeit pro `solve_building_energy()`-Call reduzieren.
2. Performance: `calc_energy_demand()`/`has_demand()` gezielt analysieren, aber nur mit Golden Regression.
3. Tests: gezielte Unit-Tests fuer `building_ventilation.py`, `building_lighting.py`, `building_energy.py` ergaenzen.
4. Architektur: Restmethoden in `building.py` pruefen, ob weitere reine Helper ausgelagert werden sollten.

Empfehlung: Vor neuer Performance-Arbeit zuerst gezielte Unit-Tests fuer die ausgelagerten Module schreiben, damit spaetere Optimierungen sicherer sind.

## Folgeplan nach B-S7

Dieser Folgeplan ist absichtlich getrennt vom reinen Split. B-S1 bis B-S7 haben die Architektur vorbereitet; die naechsten Schritte sollen entweder Absicherung oder gezielte Performance-Arbeit sein.

### B-F1: Unit-Tests fuer ausgelagerte Helper-Module

#### Ziel

Die neu ausgelagerten Module separat absichern, bevor weitere Performance-Aenderungen im thermischen Pfad passieren.

#### Betroffene Module

- `building_ventilation.py`
- `building_lighting.py`
- `building_heat_flow.py`
- `building_energy.py`

#### Sinnvolle Tests

- `building_ventilation.py`: Nutzungszeit normal, Nutzungszeit ueber Mitternacht, reine Infiltration, Night-Flushing mit `t_set_heating = 0`.
- `building_lighting.py`: Licht an/aus bei Lux-Grenze und Occupancy.
- `building_heat_flow.py`: Heating-Pfad, Cooling-Pfad, gesetzte Supply-Temperaturen.
- `building_energy.py`: kein Demand, Heating Demand, Cooling Demand mit minimalem Fake-Building oder bestehenden Fixtures.

#### Prioritaet

Hoch. Diese Tests reduzieren Risiko fuer spaetere Optimierungen.

#### Status

Umgesetzt.

Neue Testdatei:

```text
tests/building_simulator/test_building_helper_modules.py
```

Abgedeckt:

- `building_ventilation.py`: normale Nutzungszeit, Nutzungszeit ueber Mitternacht, reine Infiltration, Night-Flushing mit `t_set_heating = 0`.
- `building_lighting.py`: Lichtbedarf an/aus anhand Lux-Grenze und Occupancy.
- `building_heat_flow.py`: Emission-Flows werden auf `phi_ia`, `phi_st`, `phi_m` addiert und Supply-Temperaturen gesetzt.
- `building_energy.py`: kein Heating/Cooling Demand setzt alle Energy-Totals auf 0; unrestricted demand nutzt den 10-W/m2-Referenzfall.

Technisch geprueft:

```powershell
python -c "import ast, pathlib; ast.parse(pathlib.Path(r'tests\building_simulator\test_building_helper_modules.py').read_text(encoding='utf-8')); print('syntax ok')"
```

Vom Nutzer auszufuehren:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_building_helper_modules.py
python -m pytest -q -p no:cacheprovider tests\building_simulator
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

### B-F2: Restmethoden in `building.py` pruefen

#### Ziel

Nach dem ersten Split pruefen, ob weitere reine Helper noch sinnvoll ausgelagert werden koennen.

#### Kandidaten

- `calc_t_m_next()`
- `calc_phi_m_tot()`
- `calc_t_m()`
- `calc_t_s()`
- `calc_t_air()`

#### Bewertung

Diese Methoden wirken historisch/kompatibilitaetsnah, weil der aktive schnelle Pfad in `calc_temperatures_crank_nicolson()` bereits inline rechnet. Erst pruefen, ob sie noch direkt benutzt werden, bevor man sie verschiebt oder entfernt.

#### Prioritaet

Mittel.

#### Status

Umgesetzt als Analyse-/Dokumentationsschritt.

Geprueft mit:

```powershell
rg "calc_t_m_next|calc_phi_m_tot|calc_t_m\(|calc_t_s\(|calc_t_air\(" src tests scripts -n
rg "h_tr_1|h_tr_2|h_tr_3|t_opperative" src/dibs_computing_core/iso_simulator/model/building.py -n
```

Ergebnis:

- `calc_t_m_next()`, `calc_phi_m_tot()`, `calc_t_m()`, `calc_t_s()` und `calc_t_air()` werden im aktiven Codepfad nicht direkt aufgerufen.
- Der aktive Stundenpfad rechnet in `calc_temperatures_crank_nicolson()` bereits inline und gibt weiter `self.t_m`, `self.t_air` und `self.t_opperative` zurueck.
- `t_opperative` bleibt dadurch aktiv relevant.
- `h_tr_1`, `h_tr_2` und `h_tr_3` haengen aktuell vor allem an den Legacy-Temperaturhelpern.

Entscheidung:

- Keine Auslagerung und keine Entfernung in B-F2, weil diese Methoden Teil der bestehenden `Building`-API sein koennen.
- Die Methoden bleiben als Legacy-Kompatibilitaet im `Building`-Objekt.
- Ein kurzer Code-Kommentar markiert, dass der aktive Rechenpfad in `calc_temperatures_crank_nicolson()` liegt.
- Wenn sie spaeter entfernt werden sollen, dann separat als B-F2b mit breiter Testausfuehrung und Golden Regression.

### B-F3: Energy-Pfad gezielt analysieren

#### Ziel

Den dominanten Hotspot `solve_building_energy()` weiter verstehen, ohne direkt Formeln zu veraendern.

#### Fragen

- Welche Arbeit passiert pro Call wirklich?
- Welche Werte sind pro Building konstant?
- Welche Objektallokationen bleiben nach P5 noch uebrig?
- Kann `calc_energy_demand()` intern klarer getrennt werden, ohne die ISO-Logik zu aendern?

#### Prioritaet

Hoch fuer Performance, aber erst nach B-F1.

#### Status

Umgesetzt als Analyse-/Dokumentationsschritt.

Gepruefte Dateien:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/model/building.py`
- `src/dibs_computing_core/iso_simulator/model/building_energy.py`
- `src/dibs_computing_core/iso_simulator/model/building_heat_flow.py`

Aktiver Call-Pfad pro Stunde:

```text
BuildingSimulator.calc_energy_demand_for_time_step()
  -> Building.solve_building_energy()
    -> has_demand()
      -> calc_temperatures_crank_nicolson(energy_demand=0)
        -> calc_heat_flow()
    -> optional calc_energy_demand(), wenn Heating oder Cooling Demand aktiv ist
      -> calc_temperatures_crank_nicolson(energy_demand=0)
        -> calc_heat_flow()
      -> calc_temperatures_crank_nicolson(energy_demand=10 W/m2 reference)
        -> calc_heat_flow()
      -> calc_energy_demand_unrestricted()
      -> calc_temperatures_crank_nicolson(final energy_demand)
        -> calc_heat_flow()
    -> optional Supply-System-Aufbau und `calc_system()`
```

Beobachtung aus Profiling:

- `solve_building_energy()` bleibt der groesste Sammel-Hotspot, weil er Demand-Pruefung, Energiebedarf, Supply-System und Ergebnis-State zusammenfuehrt.
- `has_demand()` ist teuer, weil es bereits eine vollstaendige Temperaturrechnung mit `energy_demand=0` ausfuehrt.
- `calc_energy_demand()` fuehrt bei aktiver Last erneut `energy_demand=0` aus, obwohl `has_demand()` direkt davor denselben Null-Fall berechnet hat.
- Dadurch gibt es bei Demand-Stunden eine offensichtliche Doppelarbeit: Null-Fall wird in `has_demand()` und danach nochmal in `calc_energy_demand()` gerechnet.
- Jede Temperaturrechnung ruft `calc_heat_flow()` auf. Deshalb steigen `calc_temperatures_crank_nicolson()` und `calc_heat_flow()` proportional zu dieser Mehrfachrechnung.
- `calc_energy_demand_unrestricted()` selbst ist klein; der relevante Aufwand liegt nicht dort, sondern in den Temperaturfaellen davor/danach.
- Die Director-Objekte wurden bereits in B-S7/B-F1 reduziert; verbleibende Allokationen kommen vor allem von Supply-/Emission-Systeminstanzen pro Temperatur- bzw. Demand-Fall.

Sichere Optimierungsidee fuer B-F4:

- Den Null-Fall aus `has_demand()` wiederverwenden, statt ihn in `calc_energy_demand()` direkt nochmal zu berechnen.
- Dafuer sollte `has_demand()` neben dem gesetzten State auch den berechneten `t_air_0`-Wert auf dem Building speichern, z. B. `_last_no_demand_t_air` oder aehnlich.
- `calc_energy_demand()` kann diesen Wert dann nutzen, wenn er zum gleichen Stundenkontext gehoert.
- Wichtig: sehr vorsichtig umsetzen, weil `calc_temperatures_crank_nicolson()` stateful ist und `self.t_m`, `self.t_air`, `self.t_s`, `self.phi_*` setzt.
- Nach der Wiederverwendung muss der finale Temperaturzustand weiterhin durch den finalen `calc_temperatures_crank_nicolson(self.energy_demand, ...)` gesetzt werden.

Risiko:

- Mittel. Die Formeln bleiben gleich, aber State-Reihenfolge ist empfindlich.
- Golden Regression ist Pflicht.
- Unit-Test fuer den Wiederverwendungsfall ist sinnvoll, damit `calc_temperatures_crank_nicolson(0, ...)` nicht doppelt laeuft.

Erwarteter Effekt:

- Weniger `calc_temperatures_crank_nicolson()`- und `calc_heat_flow()`-Calls in Demand-Stunden.
- Potenziell sichtbarer als kleinere Micro-Optimierungen, weil die Profiling-Daten zeigen, dass diese beiden Methoden zusammen einen grossen Anteil ausmachen.

B-F3-Entscheidung:

- Keine Logik in B-F3 geaendert.
- Naechster sinnvoller Schritt ist B-F4: Null-Fall aus `has_demand()` in `calc_energy_demand()` wiederverwenden.

### B-F4: Kleine Performance-Optimierungen nur mit Golden Regression

#### Moegliche Kandidaten

- konstante Faktoren fuer Lighting vorberechnen;
- konstante Faktoren fuer Ventilation vorberechnen;
- verbliebene Supply-/Emission-Allokationen messen;
- `calc_energy_demand()` auf vermeidbare Attributzugriffe pruefen.

#### Status B-F4.1

Umgesetzt: Null-Fall aus `has_demand()` wird in `calc_energy_demand()` wiederverwendet.

Geaenderte Dateien:

- `src/dibs_computing_core/iso_simulator/model/building_energy.py`
- `tests/building_simulator/test_building_helper_modules.py`

Was geaendert wurde:

- `has_demand()` speichert nach `calc_temperatures_crank_nicolson(0, ...)` den berechneten `t_air` zusammen mit dem Stundenkontext.
- `calc_energy_demand()` nutzt diesen gespeicherten `t_air_0`, wenn `internal_gains`, `solar_gains`, `t_out` und `t_m_prev` identisch sind.
- Falls `calc_energy_demand()` direkt oder mit anderem Kontext aufgerufen wird, bleibt der alte Fallback aktiv und der Null-Fall wird normal berechnet.
- Die finale Temperaturrechnung mit `self.energy_demand` bleibt unveraendert, damit der finale Building-State korrekt gesetzt wird.

Warum:

- Vorher wurde bei Demand-Stunden der Null-Fall zweimal berechnet: einmal in `has_demand()` und direkt danach nochmal in `calc_energy_demand()`.
- Jede dieser Rechnungen triggert `calc_temperatures_crank_nicolson()` und damit `calc_heat_flow()`.
- Die Optimierung reduziert also Arbeit im Hot Path, ohne die Formel zu aendern.

Testschutz:

- Neuer Unit-Test `test_energy_demand_reuses_no_demand_temperature_from_has_demand()` stellt sicher, dass `calc_energy_demand()` den Null-Fall nicht erneut berechnet, wenn der Kontext aus `has_demand()` vorhanden ist.

Erwartung nach Tests:

```text
regression_csv_golden.py -> differences=0
profile_building_hotspots.py -> weniger calc_temperatures_crank_nicolson/calc_heat_flow Calls in Demand-Stunden
```

Gemessenes Profiling nach B-F4.1:

```text
buildings=9
simulation_time_s=16.352131 wall_time_s=16.352381
solve_building_energy              calls=78840  total_s=5.848299 share=34.6281%
calc_temperatures_crank_nicolson   calls=222696 total_s=3.417226 share=20.2336%
calc_energy_demand                 calls=71928  total_s=2.754176 share=16.3076%
has_demand                         calls=78840  total_s=2.402609 share=14.2260%
calc_heat_flow                     calls=222696 total_s=1.513678 share=8.9626%
```

Vergleich gegen vorheriges Profiling:

```text
calc_temperatures_crank_nicolson: 294624 -> 222696 calls (-71928)
calc_heat_flow:                   294624 -> 222696 calls (-71928)
```

Bewertung:

- Die Call-Reduktion entspricht exakt der Anzahl der `calc_energy_demand()`-Calls.
- Damit ist bestaetigt, dass pro Demand-Stunde ein doppelter Null-Fall entfernt wurde.
- Die absolute Laufzeit ist wegen Systemzustand/Laptop-Leistung nicht direkt mit vorherigen Messungen vergleichbar.
- Fuer B-F4.1 ist die Call-Reduktion der belastbare Nachweis.

Naechster Hotspot nach B-F4.1:

- `has_demand()` hat relativ an Anteil gewonnen, weil dort weiterhin der erste Null-Fall berechnet wird.
- Naechster sinnvoller Schritt ist B-F5: pruefen, ob `has_demand()` selbst nur strukturell vereinfacht werden kann, ohne die Temperaturformel anzufassen.

#### Status B-F5

Umgesetzt: Demand-Flag-Entscheidung in `has_demand()` strukturell vereinfacht.

Geaenderte Dateien:

- `src/dibs_computing_core/iso_simulator/model/building_energy.py`
- `tests/building_simulator/test_building_helper_modules.py`

Was geaendert wurde:

- Neue kleine Helper-Funktion `_demand_flags(t_air_rounded, t_set_heating, t_set_cooling)`.
- `has_demand()` setzt `has_heating_demand` und `has_cooling_demand` jetzt ueber diese Helper-Funktion.
- Der gespeicherte Null-Fall nutzt lokal `t_air`, damit `self.t_air` nicht mehrfach gelesen werden muss.
- Die Temperaturrechnung selbst bleibt unveraendert.

Warum:

- Die alte `if/elif/else`-Logik war korrekt, aber in `has_demand()` versteckt.
- Durch den Helper ist die Demand-Entscheidung isoliert testbar.
- Die urspruengliche Heating-Prioritaet bleibt erhalten: Wenn Heating greift, wird Cooling nicht gleichzeitig gesetzt.

Testschutz:

- Neuer Unit-Test `test_demand_flags_keep_original_heating_priority()` prueft Heating, Cooling, Neutralfall und die urspruengliche Heating-Prioritaet.

Erwarteter Effekt:

- Kleine Readability-/Testbarkeitsverbesserung.
- Kein grosser Call-Count-Effekt, weil `has_demand()` weiterhin genau eine Null-Fall-Temperaturrechnung ausfuehren muss.

#### Regel

Jede Optimierung einzeln umsetzen und danach ausfuehren:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
python scripts\profile_building_hotspots.py
```

Erwartung:

```text
differences=0
```

### Empfohlene naechste Reihenfolge

1. B-F1 Unit-Tests fuer ausgelagerte Helper-Module.
2. B-F2 Restmethoden in `building.py` pruefen.
3. B-F3 Energy-Pfad gezielt analysieren.
4. B-F4 einzelne Performance-Optimierungen umsetzen.
## Reihenfolge

Empfohlene Umsetzung:

1. B-S1 `thermal_core.py`
2. B-S5 `building_lighting.py`
3. B-S4 `building_ventilation.py`
4. B-S3 `building_heat_flow.py`
5. B-S2 `building_energy.py`
6. B-S6 Building-Orchestrator aufraeumen
7. B-S7 Profiling neu bewerten

Warum diese Reihenfolge?

- Erst die risikoarmen, isolierten Teile.
- Energy-Demand zuletzt, weil dort die meisten Ergebnisrisiken liegen.
- Nach jedem Schritt bleibt die Regression klein und kontrollierbar.

## Status

B-S1 bis B-S7 sind umgesetzt bzw. dokumentiert. Weitere Schritte sollten auf Basis der B-S7-Bewertung separat geplant werden.
## Abschlussstatus Building-Split

Status: abgeschlossen fuer den aktuellen Arbeitsblock.

Umgesetzte Schritte:

- B-S1 bis B-S7: `building.py` in fokussierte Helper-Module aufgeteilt und dokumentiert.
- B-F1: gezielte Unit-Tests fuer ausgelagerte Helper-Module ergaenzt.
- B-F2: Restmethoden in `building.py` analysiert und als Legacy-Kompatibilitaet belassen.
- B-F3: Energy-Pfad analysiert und Doppelarbeit im Null-Fall identifiziert.
- B-F4.1: Null-Fall aus `has_demand()` in `calc_energy_demand()` wiederverwendet.
- B-F5: Demand-Flag-Entscheidung in `has_demand()` strukturell vereinfacht und isoliert testbar gemacht.

Finale Validierung:

```text
regression_csv_golden.py -> differences=0
```

Bewertung:

- Verhalten ist gegen Golden Regression abgesichert.
- Der wichtigste nachgewiesene Performance-Effekt ist die Call-Reduktion in B-F4.1:
  - `calc_temperatures_crank_nicolson`: `294624 -> 222696 calls`
  - `calc_heat_flow`: `294624 -> 222696 calls`
- Weitere Laufzeitvergleiche sollten nur unter stabilen Systembedingungen bewertet werden.

Naechste Arbeit ausserhalb dieses Plans:

- Weitere Performance-Arbeit separat planen, z. B. Supply-/Emission-Systeminstanzen oder Result-Objekt-Aufbau.
- Keine weiteren Aenderungen an diesem Split-Plan notwendig, solange keine neuen Building-Model-Refactorings gestartet werden.