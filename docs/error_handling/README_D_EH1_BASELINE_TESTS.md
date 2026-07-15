# D-EH1: Baseline-Tests fuer das aktuelle Fehlerverhalten

## Ziel

Diese Tests dokumentieren das Verhalten vor der eigentlichen
Error-Handling-Migration. Sie korrigieren noch keinen Produktionscode.

## Testdaten

Die Tests verwenden kleine Python-Testobjekte und keine Datenbank. Damit wird
jeder Fehlerpfad isoliert und reproduzierbar getestet. Der Konstruktor von
`BuildingSimulator` wird bewusst umgangen, weil Wetterdaten fuer die hier
geprueften Entscheidungen nicht relevant sind.

## Abgedeckte Faelle

| Fall | Aktuell festgehaltenes Verhalten |
|---|---|
| `energy_ref_area == -8` | Meldung auf stdout, Fehler wird verschluckt, Rueckgabe `None` |
| `heating_supply_system == NoHeating` | Meldung auf stdout, Fehler wird verschluckt, Rueckgabe `None` |
| gueltige Heizkonfiguration | keine Ausgabe, Rueckgabe `None` |
| unbekanntes Heizsystem | GHG-Fehler wird gedruckt und verschluckt, Rueckgabe `None` |
| unbekanntes Kuehlsystem | GHG-Fehler wird gedruckt und verschluckt, Rueckgabe `None` |
| alte Exception-Konstruktoren | `__int__` setzt `value` nicht |
| `UsageTimeError` | setzt bereits heute `value` |

## Noch nicht im Core isoliert testbar

Fehlende PLZ, unbekannte HK-/UK-Kombinationen und fehlende Nutzungszeiten
werden von konkreten `DataSource`-Implementierungen erkannt. Dieses Repository
enthaelt nur das abstrakte `DataSource`-Interface. Die echten DB-Fehlerpfade
werden deshalb spaeter mit der Lezbau-`DjangoDataSource` als Integrationstest
abgesichert.

Eine vollstaendige gueltige 8760-Stunden-Simulation wird als Golden-Snapshot-
Regression in D-EH10 verglichen. D-EH1 konzentriert sich auf das aktuelle
Fehlerverhalten; dadurch bleibt der erste Schritt klein und eindeutig.

## Warum diese Tests spaeter angepasst werden

Die Tests sind Charakterisierungstests. Nach D-EH2 bis D-EH4 soll das heutige
`print-and-continue` durch typisierte Exceptions ersetzt werden. Dann werden
die entsprechenden Erwartungen bewusst von `stdout + None` auf
`pytest.raises(...)` umgestellt.

## Ausfuehrung

```powershell
pytest -q tests/error_handling/test_current_error_behavior.py
```
