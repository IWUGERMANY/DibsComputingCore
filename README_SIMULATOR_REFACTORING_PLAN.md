# BuildingSimulator Refactoring Plan

## Ziel

Dieser Plan beschreibt Refactorings fuer
`iso_simulator/building_simulator/simulator.py`. Im Vordergrund stehen
Lesbarkeit, Modularitaet, Wiederverwendbarkeit und ein klarerer fachlicher
Aufbau.

Die mathematischen Formeln, ihre Auswertungsreihenfolge und die fachlichen
Simulationsergebnisse duerfen dabei nicht veraendert werden.

## Ausgangslage

`BuildingSimulator` umfasst etwa 1.258 Zeilen und mehr als 60 Methoden. Die
Klasse uebernimmt derzeit mehrere Verantwortlichkeiten:

- Aufbau der Fensterobjekte;
- Wetter- und Sonnenstandsdaten;
- Belegung und interne Gewinne;
- Beleuchtung und solare Gewinne;
- Warmwasser;
- Heiz- und Kuehlsystemklassifikation;
- Energietraegerzuordnung;
- GWP-, Primaerenergie- und Heizwertfaktoren;
- Aggregation von Systemenergien.

Die Klasse funktioniert als Orchestrator, enthaelt aber gleichzeitig viele
Detailentscheidungen und wiederholte Klassifikationslogik.

## P1: Direkten Building-Zugriff vereinfachen

### Problem

Viele Methoden greifen wiederholt ueber folgende Kette zu:

```python
self.datasource.building
```

### Umsetzung

Im Konstruktor eine klare Gebaeudereferenz setzen:

```python
self.building = datasource.building
```

Danach koennen Methoden beispielsweise verwenden:

```python
self.building.energy_ref_area
self.building.cooling_supply_system
```

### Nutzen

- kuerzere Ausdruecke;
- klarere Abhaengigkeit des Simulators von genau einem Gebaeude;
- einfachere Tests;
- Vorbereitung auf spaetere Komponenten.

### Risiko

Niedrig. Es muss sichergestellt werden, dass die DataSource waehrend einer
Simulation nicht nachtraeglich auf ein anderes Gebaeude umgestellt wird.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `tests/error_handling/test_error_propagation.py`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\error_handling\test_error_propagation.py
python -m pytest -q -p no:cacheprovider tests\error_handling\test_typed_simulation_errors.py
```

## P2: Window-Builder zusammenfuehren

### Problem

Folgende Methoden unterscheiden sich fast nur durch Azimut und Flaeche:

- `build_south_window()`
- `build_east_window()`
- `build_west_window()`
- `build_north_window()`

### Umsetzung

Eine gemeinsame Factory einfuehren:

```python
def _build_window(self, azimuth: float, area: float) -> Window:
    return Window(
        azimuth,
        90,
        self.building.glass_solar_transmittance,
        self.building.glass_solar_shading_transmittance,
        self.building.glass_light_transmittance,
        area,
    )
```

Die historischen Methoden koennen vorerst als kompatible Wrapper bestehen
bleiben.

### Nutzen

- weniger Duplikation;
- neue Orientierungen lassen sich einfacher ergaenzen;
- gemeinsame Fenstereigenschaften stehen nur an einer Stelle.

### Risiko

Niedrig. Orientierung und bisherige Reihenfolge der vier Fenster muessen
unveraendert bleiben.

### Status

Umgesetzt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`
- `tests/building_simulator/test_window_builders.py`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_builders.py
```

Fachliche Regression empfohlen:

- einmal `DIBS.multi()` mit `SimulationData_Breitenerhebung.csv` ausfuehren und die Summary-Ergebnisse gegen den letzten Snapshot vergleichen.

## P3: Cooling- und Heating-Fuel-Mappings zentralisieren

### Problem

Viele kleine Methoden pruefen einzelne Systeme oder Systemgruppen, bevor
`choose_the_fuel_type()` beziehungsweise
`choose_cooling_energy_fuel_type()` einen Energietraeger zurueckgeben.

Beispiele:

- `air_cool()`
- `district_cooling()`
- `gas_engine_piston_scroll()`
- `no_cooling()`
- `biogas_boiler_types()`
- `oil_boiler_types()`
- `wood()`

### Umsetzung

Systemnamen zentral Energietraegern zuordnen:

```python
COOLING_FUEL_TYPES = {
    "AirCooledPistonScroll": "Electricity grid mix",
    "AirCooledPistonScrollMulti": "Electricity grid mix",
    "WaterCooledPistonScroll": "Electricity grid mix",
    "DirectCooler": "Electricity grid mix",
    "AbsorptionRefrigerationSystem": "Waste Heat generated close to building",
    "DistrictCooling": "District cooling",
    "GasEnginePistonScroll": "Natural gas",
    "NoCooling": "None",
}
```

Unbekannte Systeme muessen weiterhin `UnsupportedSystemError` mit
`building_id`, Systemname und Phase ausloesen.

### Nutzen

- die vollstaendige Zuordnung ist an einer Stelle sichtbar;
- weniger Methoden und Verzweigungen;
- Systemerweiterungen werden einfacher;
- Mapping kann direkt parametrisiert getestet werden.

### Risiko

Mittel. Reihenfolge, Sonderfaelle und historische Systemnamen muessen exakt
erhalten bleiben.

### Status

Umgesetzt. Die Fuel-Mappings liegen in `system_fuel_mappings.py`. Die alten Fuel-Classification-Wrapper wie `air_cool()`, `district_cooling()` und `biogas_boiler_types()` wurden entfernt; `choose_the_fuel_type()` und `choose_cooling_energy_fuel_type()` sind jetzt die zentralen Zugriffe.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/system_fuel_mappings.py`
- `tests/building_simulator/test_fuel_type_mappings.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
python -m pytest -q -p no:cacheprovider tests\error_handling\test_error_propagation.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P4: Window-Gains als benanntes Ergebnis zurueckgeben

### Problem

`calc_window_gains_and_illuminance_for_all_windows()` berechnet zwei
fachliche Summen und gab sie bisher positionsabhaengig zurueck. Auch bei zwei
Werten ist das im Hotloop schwerer zu lesen, weil nicht direkt sichtbar ist,
welcher Wert Solarenergie und welcher Beleuchtungs-Illuminanz ist.

### Umsetzung

Ein schlankes `NamedTuple` einfuehren:

```python
class WindowGainsResult(NamedTuple):
    solar_gains_total: float
    transmitted_illuminance_total: float
```

Aufrufer verwenden dann benannte Attribute:

```python
window_gains = simulator.calc_window_gains_and_illuminance_for_all_windows(...)
solar_total = window_gains.solar_gains_total
illuminance_total = window_gains.transmitted_illuminance_total
```

Die einzelnen Fenstergewinne fuer Sued/Ost/West/Nord bleiben unveraendert auf
den vier `Window`-Objekten und werden weiterhin dort ausgelesen.

### Nutzen

- keine positionsabhaengige Tuple-Zerlegung;
- fachliche Bedeutung jedes Wertes ist sichtbar;
- einfachere Erweiterbarkeit und Tests.

### Risiko

Mittel, weil der Hotloop betroffen ist. Objektallokation und Laufzeit muessen
gemessen werden. Falls notwendig, kann ein `NamedTuple` oder ein schlanker
Slots-Datentyp verwendet werden.

### Status

Umgesetzt. Die Methode liefert jetzt ein schlankes `NamedTuple`
`WindowGainsResult` mit benannten Feldern statt eines anonymen Tuple.
Die fachliche Berechnung bleibt unveraendert; nur die Rueckgabe und die
Aufrufstelle im DIBS-Hotloop wurden lesbarer gemacht.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/dibs/dibs_utils/dibs_auxiliary_functions.py`
- `tests/building_simulator/test_window_gains_result.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_gains_result.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_builders.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P5: Warmwasserlogik zerlegen

### Problem

`calc_hot_water_usage()` enthaelt in einer Methode:

- Pruefung auf Warmwassersystem;
- Berechnung des Bedarfs;
- zentrale Kopplung an das Heizsystem;
- dezentrale elektrische Systeme;
- dezentrale brennstoffbasierte Systeme;
- Strom- und Brennstoffwerte.

### Umsetzung

Die Methode intern in fachliche Schritte zerlegen:

```python
_has_hot_water_system()
_calculate_hot_water_demand()
_calculate_central_hot_water_energy()
_calculate_decentral_hot_water_energy()
```

`calc_hot_water_usage()` bleibt die oeffentliche Orchestrierung und behaelt
ihre bisherige Rueckgabe.

### Nutzen

- einzelne Sonderfaelle werden separat testbar;
- weniger verschachtelte Bedingungen;
- klare Trennung zwischen Bedarf und Versorgung.

### Risiko

Mittel bis hoch. Die Reihenfolge der Berechnungen und die Behandlung von
Nullbedarf muessen exakt erhalten bleiben.

### Status

Umgesetzt. `calc_hot_water_usage()` bleibt die oeffentliche Methode mit
unveraenderter Rueckgabe, delegiert intern aber an kleinere private Methoden:

- `_has_hot_water_system()`
- `_calculate_hot_water_demand()`
- `_calculate_hot_water_energy()`
- `_uses_electric_hot_water_energy()`
- `_split_hot_water_energy_by_system()`

Damit sind die fachlichen Einzelentscheidungen isoliert testbar, ohne den
DIBS-Hotloop oder die Ergebnisstruktur zu veraendern.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `tests/building_simulator/test_hot_water_usage.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_hot_water_usage.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P6: Dreifache Systemauswertung zusammenfuehren

### Problem

Diese Methoden enthalten strukturell sehr aehnliche Berechnungen:

- `check_heating_sys_electricity_sum()`
- `check_hotwater_sys_electricity_sum()`
- `check_cooling_system_electricity_sum()`

### Umsetzung

Eine gemeinsame interne Funktion fuer Strom, Brennstoff, GWP und
Primaerenergie einfuehren:

```python
def _calculate_system_totals(
    electricity: float,
    fossils: float,
    f_hs_hi: float,
    f_ghg: float,
    f_pe: float,
) -> SystemTotals:
    ...
```

Heizung, Warmwasser und Kuehlung liefern die jeweils relevanten Eingangswerte.
Fachliche Sonderfaelle bleiben in ihren bestehenden Wrappern.

### Nutzen

- weniger dreifache Formellogik;
- Korrekturen muessen nur einmal erfolgen;
- einheitliches Ergebnisobjekt.

### Risiko

Hoch. Vorher muessen Golden-Tests fuer alle drei Energiearten existieren.

### Status

Umgesetzt. Die gemeinsame Berechnung liegt jetzt in
`_calculate_system_energy_totals()` und gibt ein benanntes `SystemEnergyTotals`
zurueck. Die drei historischen Methoden bleiben als kompatible Wrapper erhalten:

- `check_heating_sys_electricity_sum()`
- `check_hotwater_sys_electricity_sum()`
- `check_cooling_system_electricity_sum()`

Wichtig: Die historische Rueckgabe-Reihenfolge wurde bewusst erhalten.
Heating/Cooling geben `carbon` vor `primary_energy` zurueck, HotWater gibt
`primary_energy` vor `carbon` zurueck.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `tests/building_simulator/test_system_energy_totals.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_energy_totals.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_builders.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_gains_result.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_occupancy_and_gains_calculator.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P7: Faktoraufloesung zentralisieren

### Problem

Verwandte Faktoren werden ueber mehrere Methoden ermittelt:

- `get_ghg_factor_heating()`
- `get_pe_factor_heating()`
- `get_conversion_factor_heating()`
- `get_ghg_pe_conversion_factors()`

### Umsetzung

Ein benanntes Ergebnis einfuehren:

```python
@dataclass(frozen=True)
class EnergyFactors:
    ghg: float
    primary_energy: float
    hs_hi: float
    fuel_type: str
```

Eine Methode liefert alle Faktoren gemeinsam:

```python
factors = self.get_energy_factors(fuel_type)
```

### Nutzen

- Faktoren koennen nicht versehentlich aus unterschiedlichen Datensaetzen
  kombiniert werden;
- weniger wiederholte Suche;
- benannte statt positionsabhaengige Werte.

### Risiko

Mittel.

### Status

Umgesetzt. `get_energy_factors()` liefert jetzt ein benanntes `EnergyFactors`-Objekt
mit `ghg`, `primary_energy`, `hs_hi` und `fuel_type`. Die bestehenden Methoden
bleiben kompatibel:

- `get_ghg_factor_heating()`
- `get_pe_factor_heating()`
- `get_conversion_factor_heating()`
- `get_ghg_pe_conversion_factors()`

`get_ghg_pe_conversion_factors()` gibt ein `NamedTuple` zurueck und kann deshalb
weiterhin positionsbasiert entpackt werden:

```python
f_ghg, f_pe, f_hs_hi, fuel_type = simulator.get_ghg_pe_conversion_factors(fuel_type)
```

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `tests/building_simulator/test_energy_factors.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_energy_factors.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P8: Systemnamen zentral definieren

### Problem

Fachliche Werte werden an vielen Stellen als freie Strings verwendet:

```python
"NoCooling"
"DistrictCooling"
"Natural gas"
"Electricity grid mix"
```

### Umsetzung

Zunaechst zentrale Konstanten oder `frozenset`-Gruppen einfuehren. Enums
koennen spaeter folgen, wenn alle externen DataSources darauf vorbereitet sind.

### Nutzen

- weniger Tippfehler;
- eine Quelle fuer erlaubte Systemnamen;
- einfachere Validierung an der DataSource-Grenze.

### Risiko

Niedrig bei Konstanten, hoeher bei einer sofortigen Enum-Migration.

### Status

Umgesetzt. Der groesste Teil wurde bereits mit P3 erledigt, weil Heating- und
Cooling-Systemnamen inklusive Fuel-Mapping nach `system_fuel_mappings.py`
verschoben wurden. Der P8-Restschritt zentralisiert nun auch DHW-Systemnamen
und die in `simulator.py` direkt genutzten Fuel-Strings.

Zentralisiert wurden:

- `DHW_NO_SYSTEM_TYPES`
- `DHW_CENTRAL_TYPES`
- `DHW_DECENTRAL_ELECTRIC`
- `DHW_DECENTRAL_FUEL_BASED`
- `FUEL_ELECTRICITY_GRID_MIX`
- `FUEL_NATURAL_GAS`

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/system_fuel_mappings.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_hot_water_usage.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_fuel_type_mappings.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P9: Historische Methodennamen bereinigen

### Problem

Einige Methoden hatten historische Tippfehler in ihren Namen:

```python
solve_building_lightning()       # gemeint: lighting
sys_electricity_folssils_sum()   # gemeint: fossils
check_cooling_system_elctricity_sum()  # gemeint: electricity
```

### Umsetzung

Die korrekt benannten Methoden wurden eingefuehrt und interne Aufrufstellen auf
diese Namen umgestellt. Die alten Wrapper wurden nach der Aufrufstellen-Pruefung
entfernt, damit die oeffentliche API sauber bleibt.

Neue Namen:

- `solve_building_lighting()`
- `sys_electricity_fossils_sum()`
- `check_cooling_system_electricity_sum()`

### Nutzen

- bessere Verstaendlichkeit;
- keine Tippfehler in der aktiven API;
- weniger Compatibility-Ballast im Simulator.

### Status

Umgesetzt. Die falsch geschriebenen Wrapper sind entfernt.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/dibs/dibs_utils/dibs_auxiliary_functions.py`
- `tests/building_simulator/test_method_name_aliases.py`
- `tests/building_simulator/test_system_energy_totals.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_method_name_aliases.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_energy_totals.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_builders.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_gains_result.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_occupancy_and_gains_calculator.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

## P10: Langfristige Komponentenstruktur

Erst nach den kleinen, abgesicherten Refactorings kann die Klasse schrittweise
in Komponenten aufgeteilt werden:

```text
BuildingSimulator
|-- WindowCalculator
|-- OccupancyAndGainsCalculator
|-- HotWaterCalculator
|-- EnergyCarrierResolver
`-- SystemEnergyCalculator
```

`BuildingSimulator` bleibt Orchestrator und definiert weiterhin den Ablauf.
Die Komponenten duerfen keine eigene DataSource laden und keine
API-spezifischen Abhaengigkeiten erhalten.

### Status

Teilweise umgesetzt. Der erste risikoarme Architektur-Schnitt ist eingefuehrt:

- `EnergyCarrierResolver` kapselt Heating-/Cooling-Fuel-Aufloesung und
  Energy-Factor-Lookups.
- `HotWaterCalculator` kapselt DHW-Bedarf, DHW-Energie und Strom/Fossil-Split.
- `WindowCalculator` kapselt Fensteraufbau, Sonnenpositions-Precompute und Solar-/Illuminanzberechnung.
- `OccupancyAndGainsCalculator` kapselt Belegung, Appliance-Gains und interne Gewinne.
- `SystemEnergyCalculator` kapselt die gemeinsame Berechnung von Hi-, GHG- und
  Primaerenergie-Summen.

`BuildingSimulator` bleibt die oeffentliche Orchestrierungsschicht. Bestehende
Methoden wie `choose_the_fuel_type()`, `get_ghg_pe_conversion_factors()` und
`check_heating_sys_electricity_sum()` bleiben erhalten, delegieren intern aber
an die neuen Komponenten.

Noch nicht umgesetzt:

- keine P10-Komponente mehr offen

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/energy_carrier_resolver.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/hot_water_calculator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/occupancy_and_gains_calculator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/system_energy_calculator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/window_calculator.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `tests/building_simulator/test_energy_components.py`
- `tests/building_simulator/test_hot_water_calculator.py`
- `tests/building_simulator/test_occupancy_and_gains_calculator.py`
- `tests/building_simulator/test_window_builders.py`
- `tests/building_simulator/test_window_gains_result.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_energy_components.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_energy_factors.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_energy_totals.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_builders.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_window_gains_result.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_occupancy_and_gains_calculator.py
```

Fachliche Regression empfohlen:

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```


## P11: String-Systemnamen als Enums typisieren

### Problem

Nach P8 sind Systemnamen und Energietraeger zentralisiert, aber viele Werte
sind weiterhin freie Strings. Das ist kompatibel zu CSV/Django, aber weniger
robust gegen Tippfehler.

### Umsetzung

Es wurde eine String-kompatible Enum-Schicht eingefuehrt:

- `EnergyCarrier`
- `HeatingSystem`
- `CoolingSystem`
- `DhwSystem`

Die DataSources duerfen weiterhin Strings liefern. Resolver und Calculatoren
normalisieren Werte ueber `enum_value(...)`, sodass sowohl Strings als auch
Enum-Werte funktionieren. Oeffentliche Rueckgaben bleiben string-kompatibel.

### Nutzen

- zentrale erlaubte Werte;
- bessere Autovervollstaendigung und Lesbarkeit;
- keine harte Migration fuer CSV/Django;
- Golden-Ergebnisse bleiben stabil.

### Risiko

Niedrig bis mittel. Kritisch ist, dass CSV-/Django-Strings weiterhin exakt
akzeptiert werden und Summary-/Excel-Ausgaben keine Enum-Repraesentationen wie
`EnergyCarrier.NATURAL_GAS` enthalten.

### Status

Umgesetzt als erste sichere Enum-Migrationsschicht.

### P12-Fortsetzung

Gestartet: freie String-Verwendungen werden schrittweise durch Enum-Werte ersetzt,
ohne die DataSource- oder Ergebnis-API zu brechen. Der erste Schritt ersetzt
DHW-nahe Heating-System-Strings und den Lighting-Fuel-String durch Enum-Werte.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/system_enums.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/system_fuel_mappings.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/energy_carrier_resolver.py`
- `src/dibs_computing_core/iso_simulator/building_simulator/hot_water_calculator.py`
- `src/dibs_computing_core/iso_simulator/dibs/dibs_utils/dibs_auxiliary_functions.py`
- `tests/building_simulator/test_system_enums.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\building_simulator
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

### P12.2-Fortsetzung

Umgesetzt: weitere sichere freie String-Verwendungen wurden auf Enum-/Konstantenwerte umgestellt, ohne die DataSource- oder Ergebnis-API zu brechen.

Geaendert:

- `src/dibs_computing_core/iso_simulator/building_simulator/simulator.py`
- `src/dibs_computing_core/iso_simulator/dibs/dibs_utils/dibs_auxiliary_functions.py`
- `tests/error_handling/test_error_propagation.py`
- `README_SIMULATOR_REFACTORING_PLAN.md`

Was geaendert wurde:

- `check_energy_area_and_heating()` vergleicht `heating_supply_system` nicht mehr direkt mit `"NoHeating"`, sondern ueber `enum_value(...) == HeatingSystem.NO_HEATING.value`.
- Dadurch funktionieren weiterhin DataSource-Strings, aber auch interne `HeatingSystem.NO_HEATING`-Enum-Werte.
- Der DHW-Hotloop in `extracted_method_to_simulate_one_building()` nutzt nicht mehr `building.dhw_system not in ["NoDHW", " -"]`, sondern `enum_value(building.dhw_system) not in DHW_NO_SYSTEM_TYPES`.
- Der bestehende `BuildingNotHeatedError`-Test wurde erweitert und prueft jetzt auch `HeatingSystem.NO_HEATING`.

Bewusst nicht geaendert:

- Mapping-Dicts in `Building` enthalten weiterhin string keys. Das ist aktuell kompatibilitaetsrelevant, weil DataSourceCSV/DataSourceDjango weiterhin Strings liefern duerfen.
- Klassen- und Kommentar-Namen wie `NoHeating`, `NoCooling`, `DistrictHeating` bleiben unveraendert.

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\error_handling\test_error_propagation.py
python -m pytest -q -p no:cacheprovider tests\building_simulator\test_system_enums.py
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```$([Environment]::NewLine)
## Nicht-Ziele

Dieses Refactoring soll nicht:

- mathematische Formeln veraendern;
- Stunden parallelisieren;
- neue Energietraeger einfuehren;
- bestehende Systemnamen ohne Migration entfernen;
- DataSourceCSV oder DataSourceDjango direkt in den Core verschieben.

## Verbindliches Pruefverfahren

Nach jedem Schritt:

1. komplette pytest-Suite ausfuehren;
2. Syntax und Formatierung pruefen;
3. reale `SimulationData_Breitenerhebung.csv` ueber `DIBS.multi()` ausfuehren;
4. alle neun Gebaeude vergleichen;
5. alle 93 fachlichen Summary-Felder vergleichen;
6. stichprobenartig Stundenwerte vergleichen;
7. bei Hotloop-Aenderungen mindestens zehn Laufzeitmessungen durchfuehren;
8. Refactoring nur behalten, wenn die Ergebnisse gleich bleiben.

## Empfohlene Reihenfolge

```text
P1  Building-Referenz vereinfachen
P2  Window-Builder zusammenfuehren
P3  Fuel-Mappings zentralisieren
P4  Window-Gains-Ergebnisobjekt
P5  Warmwasserlogik zerlegen
P6  Systemauswertung zusammenfuehren
P7  Faktoraufloesung zentralisieren
P8  Systemkonstanten einfuehren
P9  historische Namen migrieren
P10 Komponenten extrahieren
P11 String-Systemnamen als Enums typisieren
```
