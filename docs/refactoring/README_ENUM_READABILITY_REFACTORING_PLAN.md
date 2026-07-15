# DIBS Core: Enum- und Readability-Refactoring-Plan

## Ziel

Diese Datei beschreibt die naechsten Refactoring-Schritte nach Abschluss des
Building-Modell-Splits. Der Fokus liegt nicht auf neuer Performance-Arbeit,
sondern auf robusterer, besser lesbarer und langfristig wartbarer Core-Logik.

Wichtig: `docs/performance/README_BUILDING_MODEL_SPLIT_PLAN.md` gilt als
abgeschlossen. Diese Datei ist ein separater Folgeblock.

## Warum dieser Block separat ist

Der Building-Split hatte das Ziel, grosse Hotloop-Methoden strukturell in
fachlich benannte Module aufzuteilen, ohne Ergebnisse zu veraendern.

Dieser neue Block hat ein anderes Ziel:

- freie String-Vergleiche schrittweise reduzieren;
- Systemtypen zentraler ueber Enums/Konstanten ausdruecken;
- lange Bedingungen lesbarer machen;
- Compatibility mit DataSourceCSV und DataSourceDjango erhalten;
- keine Fachformeln veraendern.

## Verbindliche Regel

DataSourceCSV und DataSourceDjango duerfen weiterhin Strings liefern. Der Core
muss deshalb an den Grenzen string-kompatibel bleiben.

Das bedeutet: Enums duerfen intern eingefuehrt werden, aber nicht so, dass
bestehende DataSource-Inputs brechen.

Beispiel fuer erlaubte Migration:

```python
if enum_value(building.heating_supply_system) == HeatingSystem.NO_HEATING.value:
    ...
```

Nicht gewuenscht waere ein harter Bruch wie:

```python
if building.heating_supply_system is HeatingSystem.NO_HEATING:
    ...
```

weil DataSourceCSV/DataSourceDjango aktuell weiterhin Stringwerte liefern
koennen.

## Verbindliche Pruefung nach jedem Schritt

Der Nutzer fuehrt die Tests selbst aus. Nach jedem Refactoring-Schritt sollten
mindestens diese Checks laufen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\error_handling
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

Falls ein Schritt Systemtyp-Mapping betrifft, zusaetzlich:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
```

## E-R1: Freie System-Strings weiter reduzieren

### Problem

Im Core gibt es noch direkte Vergleiche gegen Stringwerte wie `"NoHeating"`,
`"NoCooling"`, `"DistrictHeating"` oder aehnliche Systemnamen. Solche Werte
sind fachlich wichtig, aber direkte Stringvergleiche sind fehleranfaellig.

### Ziel

Direkte Stringvergleiche nur dort behalten, wo sie bewusst DataSource-Input
normalisieren. In der Core-Logik sollen zentrale Enums/Konstanten genutzt
werden.

### Vorgehen

- Stringvergleiche im Core suchen.
- Pruefen, ob es schon passende Enums/Konstanten gibt.
- Vergleich ueber `enum_value(...)` oder zentrale Constant Sets ersetzen.
- Tests fuer String-Input und Enum-Input ergaenzen.

### Risiko

Mittel. Ein falsch migrierter String kann Systemklassifikation oder Fuel-Type
Mapping veraendern.

### Prioritaet

Hoch.


### Status

Umgesetzt als erster sicherer Schritt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building.py`
- `tests/building_simulator/test_system_enums.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- `Building.class_mapping` nutzt fuer `NoHeating` und `NoCooling` jetzt `HeatingSystem.NO_HEATING.value` und `CoolingSystem.NO_COOLING.value` statt harter String-Keys.
- `Building.supply_mapping` nutzt fuer bekannte Heating-/Cooling-Systeme jetzt `HeatingSystem.*.value` und `CoolingSystem.*.value` statt harter String-Keys.
- Die Laufzeit-Keys bleiben weiterhin normale Strings, weil `.value` exakt den bisherigen DataSource-Werten entspricht.
- Ein gezielter Test prueft, dass `Building` auch mit Enum-Werten fuer `NoHeating`/`NoCooling` initialisiert werden kann.

Bewusst nicht geaendert:

- Emission-Systemnamen wurden in der E-R1-Fortsetzung ueber `EmissionSystem` zentralisiert.
- DataSourceCSV und DataSourceDjango muessen nicht angepasst werden.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```


### E-R1-Fortsetzung: Emission-System-Enum und Mapping-Auslagerung

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/system_enums.py`
- `src/dibs_computing_core/iso_simulator/model/building_system_mappings.py`
- `src/dibs_computing_core/iso_simulator/model/building.py`
- `tests/building_simulator/test_system_enums.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- Neues `EmissionSystem`-Enum fuer `AirConditioning`, `SurfaceHeatingCooling`, `ThermallyActivated`, `NoHeating` und `NoCooling`.
- `Building.class_mapping` wurde aus `Building.__init__` entfernt und als `BUILDING_EMISSION_SYSTEM_MAPPING` ausgelagert.
- `Building.supply_mapping` wurde aus `Building.__init__` entfernt und als `BUILDING_SUPPLY_SYSTEM_MAPPING` ausgelagert.
- `Building` loest Systemklassen jetzt ueber `enum_value(...)` gegen diese zentralen Mapping-Konstanten auf.
- Der Test `test_building_system_mappings_accept_system_enums()` prueft jetzt auch `EmissionSystem`-Enums fuer Emission-Systeme.

Warum:

- Die Mapping-Dicts muessen nicht pro `Building`-Instanz neu aufgebaut werden.
- Systemnamen liegen zentraler und sind leichter zu pruefen.
- DataSourceCSV/DataSourceDjango bleiben kompatibel, weil die Mapping-Keys weiterhin normale Stringwerte sind.

Bewusst nicht geaendert:

- Die Namen der Emission- und Supply-Systemklassen bleiben unveraendert.
- Es gibt keine Formel- oder Ergebnislogik-Aenderung.
- DataSourceCSV und DataSourceDjango muessen keine Enums liefern.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## E-R2: Mapping-Dicts klarer strukturieren

### Problem

Fuel-Type- und System-Mappings sind fachlich zentral. Wenn Dicts, Enums und
Compatibility-Strings an mehreren Stellen auseinanderlaufen, entstehen spaeter
schwer erkennbare Fehler.

### Ziel

Mapping-Dicts sollen eindeutig zeigen:

- welcher Input-Systemtyp akzeptiert wird;
- welcher Energy Carrier daraus wird;
- welcher Fall absichtlich nicht unterstuetzt wird;
- welche Systeme Sonderlogik brauchen.

### Vorgehen

- Bestehende Mapping-Dateien pruefen.
- Doppelte oder semantisch gleiche Gruppen zusammenziehen.
- Alte Wrapper nur behalten, wenn externe Tests oder APIs sie noch brauchen.
- Neue Tests fuer wichtige Gruppen schreiben, z. B. District Heating, District Cooling, NoHeating, NoCooling.

### Risiko

Mittel. Mapping-Fehler koennen Summary-Ergebnisse veraendern.

### Prioritaet

Hoch.


### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_system_mappings.py`
- `tests/building_simulator/test_system_enums.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- `BUILDING_SUPPLY_SYSTEM_MAPPING` ist jetzt sichtbar aus zwei fachlichen Gruppen zusammengesetzt:
  - `HEATING_SUPPLY_SYSTEM_MAPPING`
  - `COOLING_SUPPLY_SYSTEM_MAPPING`
- `BUILDING_EMISSION_SYSTEM_MAPPING` bleibt separat, weil Emission-Systeme fachlich keine Supply-Systeme sind.
- Neue Tests pruefen, dass Heating- und Cooling-Supply-Mappings disjunkt sind und dass wichtige Sonderfaelle wie `NoHeating`, `NoCooling`, `DistrictHeating` und `DistrictCooling` korrekt gemappt bleiben.

Warum:

- Die Mapping-Datei zeigt jetzt klarer, welcher Systemtyp in welche fachliche Gruppe gehoert.
- `Building` muss weiterhin nur `BUILDING_EMISSION_SYSTEM_MAPPING` und `BUILDING_SUPPLY_SYSTEM_MAPPING` kennen.
- Die oeffentliche DataSource-Kompatibilitaet bleibt unveraendert.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## E-R3: Lange Bedingungen sprechend kapseln

### Problem

Einige Methoden enthalten Bedingungen, bei denen fachliche Bedeutung und
technische Details vermischt sind. Das macht Reviews schwer und erhoeht das
Risiko bei spaeteren Aenderungen.

### Ziel

Komplexe Bedingungen sollen Namen bekommen, ohne die Formelreihenfolge oder
Ergebnislogik zu veraendern.

### Beispiel

Statt:

```python
if condition_a and condition_b and not condition_c:
    ...
```

besser:

```python
is_night_flushing_active = condition_a and condition_b and not condition_c
if is_night_flushing_active:
    ...
```

Oder, wenn es mehrfach gebraucht wird:

```python
def is_night_flushing_active(...):
    ...
```

### Kandidaten

- Systemauswahl und Fuel-Type-Entscheidungen;
- Heating-/Cooling-Demand-Bedingungen;
- Night-Flushing- und Ventilation-Bedingungen;
- DHW-Aktivierungslogik.

### Risiko

Niedrig bis mittel. Bei reiner Umbenennung niedrig, bei Extraktion in Funktionen
mittel wegen Parameter-/State-Risiko.

### Prioritaet

Mittel.


### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/model/building_ventilation.py`
- `src/dibs_computing_core/iso_simulator/model/building_energy.py`
- `tests/building_simulator/test_building_helper_modules.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- Night-Flushing-Bedingungen wurden in `_is_night_flushing_active(...)` gekapselt.
- Short-Circuit-Reihenfolge wurde explizit erhalten: `building.t_air` wird nur gelesen, wenn Night-Flushing grundsaetzlich moeglich ist.
- Die Bedingung `ach_vent == 0 and ach_win == 0` hat jetzt den sprechenden Namen `no_mechanical_or_window_air_exchange`.
- Die Energy-Demand-Grenzpruefung wurde in `_is_within_available_power(...)` gekapselt.
- Neue Tests sichern die beiden extrahierten Bedingungen ab, inklusive inaktivem Night-Flushing ohne vorhandenes `t_air`.

Warum:

- Die fachliche Bedeutung der Bedingungen ist jetzt lesbarer.
- Formeln, Grenzwerte und Call-Reihenfolge wurden nicht veraendert.
- Spaetere Reviews koennen schneller erkennen, was Bedingung und was Formel ist.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_building_helper_modules.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## E-R4: Compatibility-Layer sichtbar halten

### Problem

Der Core muss aktuell zwei Welten bedienen:

- bestehende String-Inputs aus DataSourceCSV/DataSourceDjango;
- intern zunehmend typsichere Enums/Konstanten.

Wenn diese Grenze unsichtbar wird, entstehen spaeter Missverstaendnisse.

### Ziel

Compatibility-Code soll explizit erkennbar sein. Neue Entwickler sollen sofort
sehen: Dieser Code existiert, damit alte String-Inputs weiterhin funktionieren.

### Vorgehen

- Hilfsfunktionen wie `enum_value(...)` nicht verstecken, sondern bewusst an
  den Systemgrenzen nutzen.
- Tests immer fuer String-Input und, falls relevant, Enum-Input schreiben.
- Keine DataSource-Annahme direkt in Hotloop-Formeln ziehen.

### Risiko

Niedrig.

### Prioritaet

Mittel.


### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/system_enums.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/energy_carrier_resolver.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/hot_water_calculator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/model/building.py`
- `src/dibs_computing_core/iso_simulator/dibs/dibs_utils/dibs_auxiliary_functions.py`
- `tests/building_simulator/test_system_enums.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- Neuer Helper `system_key(...)` dokumentiert die Compatibility-Grenze zwischen DataSource-Strings und internen `StringEnum`-Werten.
- Bestehender Helper `enum_value(...)` bleibt als rueckwaertskompatibler Alias erhalten.
- Systemgrenzen im Core verwenden jetzt `system_key(...)`, zum Beispiel bei Fuel-Type-Mapping, DHW-Pruefung, `NoHeating`-Pruefung und Building-System-Mapping.
- Neuer Test prueft, dass `system_key(...)` sowohl normale Strings als auch Enums auf denselben Mapping-Key normalisiert.

Warum:

- Neue Entwickler sehen direkt, wo DataSource-Strings und interne Enums kompatibel gemacht werden.
- Bestehende externe Nutzung von `enum_value(...)` bricht nicht.
- DataSourceCSV und DataSourceDjango bleiben unveraendert string-kompatibel.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
python -m pytest -q -p no:cacheprovider tests\error_handling\test_error_propagation.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## E-R5: Alte Kommentare und Docstrings an neue Struktur anpassen

### Problem

Nach Split, Error Handling und Enum-Schritten koennen Kommentare oder Docstrings
veraltet sein. Das ist keine Laufzeitfrage, aber stoert Wartbarkeit und Reviews.

### Ziel

Docstrings sollen erklaeren, was eine Methode fachlich macht und welche
Compatibility-Annahmen wichtig sind. Sie sollen nicht alte Implementierungsdetails
beschreiben, die nicht mehr stimmen.

### Vorgehen

- Nur fachlich wichtige Methoden dokumentieren.
- Keine offensichtlichen Kommentare einfuegen.
- Veraltete Kommentare entfernen oder korrigieren.
- Public-API-Methoden bevorzugt dokumentieren.

### Risiko

Niedrig.

### Prioritaet

Niedrig bis mittel.


### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/system_enums.py`
- `src/dibs_computing_core/iso_simulator/model/building_ventilation.py`
- `src/dibs_computing_core/iso_simulator/model/building_energy.py`
- `docs/refactoring/README_ENUM_READABILITY_REFACTORING_PLAN.md`

Was geaendert wurde:

- `system_enums.py` beschreibt jetzt klarer, dass Enums an DIBS-Mapping-Grenzen verwendet werden und string-kompatibel zu DataSourceCSV/DataSourceDjango bleiben.
- `EmissionSystem`, `CoolingSystem`, `HeatingSystem` und `DhwSystem` haben kurze fachliche Docstrings.
- `building_ventilation.py` enthaelt keine ueberholten Kommentare mehr; der wichtige Sonderfall bei Night-Flushing ist kurz und fachlich beschrieben.
- `building_energy.py` enthaelt weniger veraltete Schritt-/Zeilen-Kommentare und klarere Kommentare fuer Demand-Status, Referenzfall und Leistungsbegrenzung.

Bewusst nicht geaendert:

- Keine Formeln.
- Keine Ergebnislogik.
- Keine DataSource-Schnittstellen.

Empfohlene Pruefung:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_building_helper_modules.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## Nicht-Ziele

Dieser Refactoring-Block soll nicht:

- neue Fachformeln einfuehren;
- Ergebnisse veraendern;
- DataSourceCSV oder DataSourceDjango zwingen, Enums statt Strings zu liefern;
- Performance-Hotloop ohne Messung veraendern;
- grosse Architektur-Umbauten starten.

## Empfohlene Reihenfolge

```text
E-R1  Freie System-Strings weiter reduzieren
E-R2  Mapping-Dicts klarer strukturieren
E-R3  Lange Bedingungen sprechend kapseln
E-R4  Compatibility-Layer sichtbar halten
E-R5  Alte Kommentare und Docstrings an neue Struktur anpassen
```

## Aktueller Stand

Der Enum-/Readability-Block ist abgeschlossen.

Umgesetzt:

- E-R1: Freie System-Strings wurden weiter reduziert und zentrale System-Enums werden an den Mapping-Grenzen genutzt.
- E-R2: Mapping-Dicts wurden klarer strukturiert und aus `Building.__init__` ausgelagert.
- E-R3: Lange Bedingungen wurden in sprechende Helper gekapselt.
- E-R4: Der Compatibility-Layer fuer String-Inputs aus DataSourceCSV/DataSourceDjango ist sichtbar dokumentiert.
- E-R5: Kommentare und Docstrings wurden an die neue Struktur angepasst.

Letzte fachliche Erwartung:

```text
differences=0
```

Keine weiteren Schritte in dieser README offen.

Naechster sinnvoller Arbeitsblock:

- Wenn weiter an `DibsComputingCore` gearbeitet wird: neue README fuer den naechsten konkreten Refactoring- oder Optimierungsblock anlegen.
- Wenn am Datenadapter weitergearbeitet wird: in `DibsDataSourceCSV` mit `README_OPTIMIZATION_PLAN.md` oder `README_DATASOURCE_SPLIT_PLAN.md` weitermachen.

