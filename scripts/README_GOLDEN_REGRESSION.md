# Golden Regression: 9 CSV Buildings

Dieses Skript ist ein manueller Regressionstest fuer die 9 Gebaeude aus:

```text
C:\Users\wail\Desktop\Projects\Stand dibs\SimulationData_Breitenerhebung.csv
```

Es fuehrt `DIBS.multi()` aus und vergleicht alle Felder von `SummaryResult` sowie ausgewaehlte Stundenwerte gegen gespeicherte Golden-Snapshots.

Das Skript erwartet diese lokalen Schwester-Repositories neben `DibsComputingCore`:

```text
DibsDataSourceCSV\src
DibsData\src
```

Diese Pfade werden automatisch in `sys.path` gesetzt, damit `dibs_datasource_csv` und `dibs_data` importiert werden koennen.

## 1. Golden-Snapshot initial erstellen oder bewusst aktualisieren

Vom Root-Verzeichnis `DibsComputingCore` aus:

```powershell
python scripts\regression_csv_golden.py --update-golden
```

Das schreibt:

```text
tests\golden\summary_9_buildings.csv
tests\golden\hourly_sample_9_buildings.csv
```

Diesen Befehl nur ausfuehren, wenn die aktuellen Ergebnisse fachlich korrekt sind und als neuer Referenzstand gelten sollen.

## 2. Nach jeder Refactoring-Aenderung vergleichen

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
```

Das Skript schreibt zusaetzlich eine Excel-Datei:

```text
regression_results\summary_9_buildings_comparison.xlsx
```

Die Datei enthaelt:

- `Metadata`: Anzahl Gebaeude, Felder, Differenzen und Laufzeit;
- `Current`: aktuelle SummaryResult-Werte;
- `Diff`: nur abweichende Summary-Felder;
- `HourlyCurrent`: aktuelle ausgewaehlte Stundenwerte;
- `HourlyDiff`: nur abweichende Stundenwerte.

## Exit Codes

- `0`: Vergleich erfolgreich, keine Unterschiede.
- `1`: Unterschiede gefunden.
- `2`: Golden-Datei fehlt. Erst `--update-golden` ausfuehren.

## Hinweis

Das ist bewusst kein normaler schneller Unit-Test, weil die komplette 9-Gebaeude-Simulation laenger laufen kann. Er ist fuer manuelle Regression nach Refactorings gedacht.