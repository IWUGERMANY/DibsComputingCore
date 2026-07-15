# DIBS Computing Core: Fehlerbehandlung und Umsetzungsplan

## 1. Ziel

Der DIBS Computing Core soll Fehler im Datenzugriff und in der Simulation
eindeutig erkennen und als typisierte Python-Exceptions an den aufrufenden
Host weitergeben.

DIBS ist eine Bibliothek. Deshalb soll DIBS weder GraphQL- noch REST-Fehler
erzeugen und keine deutschsprachigen Frontendmeldungen festlegen.

Der Zielablauf ist:

```text
DIBS DataSource / Simulationskern
        |
        | DIBSError mit code, phase und context
        v
Lezbau DIBS-Service
        |
        | Mapping auf LezbauError
        v
GraphQL-/REST-Adapter
        |
        | sichere Frontendmeldung
        v
Frontend
```

## 2. Warum DIBS vor Lezbau bearbeitet wird

Lezbau kann einen DIBS-Fehler nur korrekt behandeln, wenn der Computing Core
den Fehler nicht verschluckt und eine stabile Fehlerkategorie liefert.

Aktuell gibt es Stellen, an denen DIBS eine Exception ausloest, sie sofort
wieder faengt, mit `print()` ausgibt und danach normal weiterlaeuft. Dadurch
kann Lezbau nicht unterscheiden, ob DIBS erfolgreich war oder ein ungueltiger
Zwischenzustand entstanden ist.

Die Reihenfolge lautet deshalb:

```text
1. DIBS-Fehlervertrag stabilisieren
2. DIBS-Fehlerwege testen
3. neue DIBS-Version beziehungsweise Commit bereitstellen
4. Lezbau auf den neuen DIBS-Fehlervertrag umstellen
5. GraphQL- und REST-Adapter in Lezbau implementieren
```

## 3. Aktueller Stand

Vorhandene Exception-Dateien:

```text
src/dibs_computing_core/iso_simulator/exceptions/
|-- building_not_heated_exception.py
|-- ghg_emission.py
|-- plz_exception.py
|-- uk_or_hk_exception.py
|-- usage_time_exception.py
`-- __init__.py
```

Vorhandene Klassen:

```text
BuildingNotHeatedError
GHGEmissionError
PLZNotFoundError
HkOrUkNotFoundError
UsageTimeError
```

## 4. Konkrete Findings

### 4.1 Fehlerhafte Konstruktoren

Vier Exception-Klassen definieren `__int__` statt `__init__`:

```python
def __int__(self, value: str):
    self.value = value
```

Betroffen sind:

```text
BuildingNotHeatedError
GHGEmissionError
PLZNotFoundError
HkOrUkNotFoundError
```

Dadurch wird die beabsichtigte Initialisierung nicht ausgefuehrt.

### 4.2 Exceptions werden verschluckt

`check_energy_area_and_heating()` verwendet aktuell:

```python
try:
    raise BuildingNotHeatedError(...)
except BuildingNotHeatedError as error:
    print(error)
```

Der Fehler verlaesst die Methode nicht. Der Aufrufer startet anschliessend
trotzdem die 8760-Stunden-Simulation.

### 4.3 GHG-Fehler liefern implizit `None`

Die Methoden zur Auswahl des Brennstofftyps fangen `GHGEmissionError` ab und
geben nur den Text aus. Nach dem `except` fehlt ein `return`, daher liefert die
Methode implizit `None` statt des angekuendigten `str`.

Moegliche Folge:

```text
unbekanntes Versorgungssystem
  -> GHGEmissionError wird gedruckt und verschluckt
  -> fuel_type wird None
  -> spaeterer KeyError/TypeError
  -> urspruengliche Ursache ist nicht mehr erkennbar
```

### 4.4 Built-in-Exceptions ohne DIBS-Kontext

Im Simulationskern werden unter anderem verwendet:

```text
ValueError
NameError
```

Beispiele:

```text
ungueltiger Lueftungszustand
Heizfunktion ohne Heiz- oder Kuehlbedarf
unbekannter Heiz-/Kuehlstatus
ungueltiges Versorgungssystem
```

Lezbau kann daraus keine stabile DIBS-Kategorie ableiten.

### 4.5 DataSource-Typannotationen beschreiben Exceptions als Rueckgabewert

Beispiel:

```python
def get_usage_time(self) -> tuple[int, int] | UsageTimeError:
```

Eine Exception wird nicht regulaer zurueckgegeben, sondern ausgeloest. Der
Rueckgabetyp soll nur den Erfolgswert beschreiben. Die Exception gehoert in
den `Raises`-Abschnitt der Dokumentation.

### 4.6 Keine gemeinsame Basisklasse

Alle vorhandenen DIBS-Exceptions erben direkt von `Exception`. Ein Host kann
daher nicht alle erwarteten DIBS-Fehler mit einem gemeinsamen Typ behandeln.

### 4.7 `print()` statt Bibliotheksvertrag

Der Core verwendet mehrere `print()`-Aufrufe. In einem Webserver oder in
Multiprocessing-Ausfuehrungen sind diese Meldungen nicht verlaesslich einem
Request oder Gebaeude zuzuordnen.

### 4.8 Keine erkennbare Exception-Testsuite

Die aktuellen Fehlerwege sind nicht durch gezielte Tests abgesichert. Eine
Umstellung von `print-and-continue` auf `raise` veraendert das Verhalten und
muss deshalb vorab getestet werden.

## 5. Auswirkungen auf die Lezbau-Modulkette

Direkt betroffen ist zunaechst DIBS. Ein verschluckter DIBS-Fehler kann aber
die nachfolgenden Module beeinflussen:

```text
DIBS
  -> stundenweise Energieprofile
  -> Profilaggregation
  -> PVSim
  -> SolarSim
  -> gemeinsame API-Antwort
```

Wenn DIBS unvollstaendige oder ungueltige Profile liefert, koennen PVSim und
SolarSim formal weiterlaufen, obwohl ihre Eingaben nicht mehr verlaesslich
sind. Deshalb muss jeder DIBS-Fehler einer Auswirkungsklasse zugeordnet werden.

## 6. Fehlerauswirkungen: fatal, partial und warning

### 6.1 Fatal

Die aktuelle Einzelgebaeude-Simulation muss abbrechen. Es existiert kein
verlaessliches DIBS-Ergebnis fuer nachgelagerte Module.

Beispiele:

```text
Gebaeude kann nicht geladen werden
Wetterdaten fehlen
Nutzungsprofil fehlt
HK-/UK-Kombination ist unbekannt
thermischer Zustand verletzt eine interne Invariante
Versorgungssystem ist fuer eine notwendige Berechnung unbekannt
```

### 6.2 Partial

Ein fachlich klar abgegrenzter Ergebnisbereich fehlt, andere Ergebnisse sind
nachweislich gueltig.

Beispiel:

```text
Energieprofile sind gueltig, aber eine optionale GHG-Auswertung ist nicht moeglich
```

Partial darf erst verwendet werden, wenn ein expliziter Ergebnisvertrag
vorhanden ist, zum Beispiel:

```python
ResultStatus(
    success=False,
    partial=True,
    unavailable_sections=("ghg_emissions",),
)
```

Solange dieser Vertrag nicht implementiert ist, muss ein solcher Fehler als
fatal gelten. Stilles Weiterrechnen ist nicht zulaessig.

### 6.3 Warning

Die Berechnung bleibt fachlich korrekt; lediglich ein optionaler Pfad oder
eine Optimierung ist nicht verfuegbar.

Beispiele:

```text
Numba ist nicht installiert und der Python-Fallback wird verwendet
optionaler Cache ist nicht verfuegbar
Performance-Optimierung wird deaktiviert
```

Warnings werden mit `logger.warning()` protokolliert und nicht als Exception
an den Host gemeldet.

## 7. Offene fachliche Entscheidung: nicht beheiztes Gebaeude

`BuildingNotHeatedError` kann zwei verschiedene Bedeutungen haben.

Variante A: Nicht beheizt ist fuer diesen Use Case ungueltig.

```python
if not heated:
    raise BuildingNotHeatedError(...)
```

Die Einzelgebaeude-Simulation bricht ab.

Variante B: Nicht beheizt ist ein erlaubter Gebaeudezustand.

```python
if not simulator.is_building_heated():
    return create_explicit_unheated_result()
```

Dann darf keine Exception als Kontrollfluss verwendet werden. DIBS muss ein
explizites und fachlich definiertes Ergebnis fuer diesen Fall liefern.

Vor der Codeaenderung muss entschieden werden, welche Variante fachlich gilt.

## 8. Zielhierarchie

Empfohlene Struktur:

```text
DIBSError
|-- DIBSInputError
|-- DIBSDataSourceError
|   |-- PLZNotFoundError
|   |-- HkOrUkNotFoundError
|   `-- UsageTimeError
|-- DIBSConfigurationError
|   |-- BuildingNotHeatedError
|   `-- UnsupportedSystemError
|-- DIBSSimulationError
|   |-- SimulationStateError
|   `-- ThermalCalculationError
`-- DIBSResultError
    `-- GHGEmissionError
```

Vorgeschlagene Basisklasse:

```python
class DIBSError(Exception):
    code = "DIBS_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        phase: str | None = None,
        context: dict | None = None,
    ):
        self.phase = phase
        self.context = context or {}
        super().__init__(message or self.code)
```

Der `context` darf nur technische, nicht sensible Informationen enthalten.

## 9. Vorgesehene Fehlercodes

| Exception | Code | Auswirkung |
|---|---|---|
| `DIBSError` | `DIBS_ERROR` | fatal |
| `DIBSInputError` | `DIBS_INVALID_INPUT` | fatal |
| `DIBSDataSourceError` | `DIBS_DATASOURCE_ERROR` | fatal |
| `PLZNotFoundError` | `DIBS_POSTCODE_NOT_FOUND` | fatal |
| `HkOrUkNotFoundError` | `DIBS_USAGE_TYPE_NOT_FOUND` | fatal |
| `UsageTimeError` | `DIBS_USAGE_TIME_NOT_FOUND` | fatal |
| `BuildingNotHeatedError` | `DIBS_BUILDING_NOT_HEATED` | offen |
| `UnsupportedSystemError` | `DIBS_UNSUPPORTED_SYSTEM` | fatal |
| `SimulationStateError` | `DIBS_INVALID_SIMULATION_STATE` | fatal |
| `ThermalCalculationError` | `DIBS_THERMAL_CALCULATION_FAILED` | fatal |
| `GHGEmissionError` | `DIBS_GHG_CALCULATION_FAILED` | fatal, spaeter eventuell partial |

## 10. Verantwortungsgrenzen

### DIBS ist verantwortlich fuer

```text
Fehler erkennen
DIBS-spezifische Exception ausloesen
stabilen Fehlercode bereitstellen
Phase und sicheren Kontext bereitstellen
urspruengliche Exception mit `raise ... from exc` erhalten
```

### DIBS ist nicht verantwortlich fuer

```text
GraphQLError
HTTP-Statuscodes
deutsche oder englische Frontendtexte
Request-ID-Erzeugung des Webservers
Benutzerberechtigungen
Frontenddarstellung
```

### Lezbau ist verantwortlich fuer

```text
DIBSError abfangen
einmal zentral loggen
DIBS-Code auf Lezbau-Fehlercode abbilden
GraphQL-/REST-Antwort erzeugen
Frontendmeldung uebersetzen
nachgelagerte Module bei fatalem DIBS-Fehler nicht starten
```

## 11. Arbeitspakete

### D-EH1: Ist-Verhalten mit Tests absichern

Status: umgesetzt. Details und Testabgrenzung stehen in
`README_D_EH1_BASELINE_TESTS.md`.

Ziel: Aktuelles Verhalten vor jeder Aenderung reproduzierbar machen.

Tests:

```text
Gebaeude mit energy_ref_area == -8
Gebaeude mit heating_supply_system == NoHeating
unbekanntes Heizsystem
unbekanntes Kuehlsystem
fehlende PLZ
unbekannte HK-/UK-Kombination
fehlende Nutzungszeit
ungueltiger thermischer Zustand
```

Die Tests sollen festhalten, ob heute `None`, `print()`, ein Folgefehler oder
eine Exception entsteht.

### D-EH2: `DIBSError` und Fehlercodes einfuehren

Status: umgesetzt.

Aufgaben:

1. Gemeinsame Basisklasse implementieren.
2. `code`, `phase` und `context` aufnehmen.
3. Bestehende Exceptions von `DIBSError` ableiten.
4. Bestehende Importpfade vorerst kompatibel halten.
5. Exceptions zentral ueber `exceptions/__init__.py` exportieren.

### D-EH3: Exception-Konstruktoren korrigieren

Status: umgesetzt.

Aufgaben:

1. Alle `__int__`-Tippfehler entfernen.
2. Einheitliche `__init__`-Signatur verwenden.
3. `super().__init__(message)` aufrufen.
4. Tests fuer `str(error)`, `error.code`, `error.phase` und `error.context` ergaenzen.

### D-EH4: `print-and-swallow` entfernen

Status: umgesetzt.

Aufgaben:

1. `BuildingNotHeatedError` nicht lokal abfangen.
2. `GHGEmissionError` nicht lokal abfangen.
3. Methoden muessen entweder einen gueltigen Wert liefern oder eine Exception ausloesen.
4. Verbleibende Debug-`print()` durch Logger oder expliziten Rueckgabestatus ersetzen.
5. Sicherstellen, dass Lezbau den Fehler empfangen kann.

### D-EH5: Built-in-Exceptions typisieren

Status: umgesetzt.

Aufgaben:

1. Lueftungszustandsfehler durch `SimulationStateError` ersetzen.
2. Heiz-/Kuehl-Invarianten durch `SimulationStateError` ersetzen.
3. Unbekannte Systeme durch `UnsupportedSystemError` ersetzen.
4. Thermische Rechenfehler durch `ThermalCalculationError` mit Exception-Chaining kapseln.
5. Programmierfehler nicht pauschal als fachliche Fehler deklarieren.

### D-EH6: DataSource-Vertrag korrigieren

Status: umgesetzt.

Aufgaben:

1. Exception-Typen aus Rueckgabeannotationen entfernen.
2. `Raises` in Docstrings dokumentieren.
3. DataSource-Implementierungen auf denselben Fehlervertrag pruefen.
4. Leere Rueckgaben und `None` nur verwenden, wenn sie fachlich erlaubt sind.
5. Fehlende Wetter-, Profil- und Typdaten als DIBS-Exceptions melden.

### D-EH7: Oeffentliche DIBS-Grenze definieren

Status: Einzelgebaeude umgesetzt. Batch- und Multiprocessing-Verhalten bleibt bewusst offen.

Betroffene Methoden:

```text
DIBS.calculate_result_of_one_building()
DIBS.calculate_result_of_all_buildings()
DIBS.multi()
DIBS.multi_with_batches()
```

Aufgaben:

1. Einzelgebaeude-Fehler unveraendert nach aussen reichen.
2. Phase `initialize_data`, `simulator_init`, `simulate_hours` oder `summary_wrap` ergaenzen.
3. Unbekannte Programmierfehler nicht verschlucken.
4. Batch-Verhalten fuer einzelne fehlerhafte Gebaeude definieren.
5. Multiprocessing-Exceptions beim Einsammeln der Async-Ergebnisse erhalten.

Empfehlung fuer Batches:

```text
Einzelgebaeude: fataler Fehler bricht den Request ab
Batch: Fehler je Gebaeude sammeln und expliziten BatchResult liefern
```

### D-EH8: Logging vereinheitlichen

Status: umgesetzt. Die temporaeren SIM_PERF-Messungen bleiben bis zum separaten Entfernen der Performance-Instrumentierung erhalten.

Aufgaben:

1. `print()` aus dem Bibliothekscode entfernen.
2. Keine globale Logging-Konfiguration in DIBS setzen.
3. Bibliothekslogger mit `logging.getLogger(__name__)` verwenden.
4. Erwartete Exceptions nicht auf jeder Schicht erneut loggen.
5. Finale Fehlerprotokollierung dem Host ueberlassen.
6. DIBS darf Debug- und Performance-Informationen weiterhin strukturiert loggen.

### D-EH9: Lezbau-Integrationsvertrag testen

Status: umgesetzt fuer den DIBS-Core-Vertrag. Der Test ist bewusst nicht nur Lezbau-spezifisch, sondern schuetzt auch DataSourceCSV und DataSourceDjango: Beide duerfen stateful bleiben und Strings/Objekte liefern, waehrend erwartete DIBS-Fehler als `DIBSError` mit `code`, `phase` und `context` an Host-Anwendungen propagieren.

Aufgaben im DIBS-Repository:

1. Oeffentliche Exception-Imports testen.
2. Fehlercodes als stabilen Vertrag dokumentieren.
3. Minimalen Beispiel-DataSource fuer Fehlertests bereitstellen.
4. Sicherstellen, dass DIBS keine GraphQL- oder Django-Abhaengigkeit erhaelt.

Umgesetzt in:

```text
tests/error_handling/test_lezbau_integration_contract.py
```

Validierung empfohlen:

```powershell
python -m pytest -q -p no:cacheprovider tests\error_handling\test_lezbau_integration_contract.py
```

Aufgaben anschliessend in Lezbau:

```python
try:
    dibs.calculate_result_of_one_building()
except DIBSError as exc:
    raise ExternalSimulationError(
        "DIBS simulation failed",
        context={
            "dibs_code": exc.code,
            "dibs_phase": exc.phase,
            **exc.context,
        },
    ) from exc
```

### D-EH10: Ergebnis- und Performance-Regression pruefen

Status: abgeschlossen.

Error Handling darf gueltige Simulationen nicht veraendern. Dieser Abschluss-Check
wurde nach D-EH9 durchgefuehrt.

Durchgefuehrte Pruefungen:

1. Error-Handling-Tests sind gruen.
2. Building-Simulator-Tests sind gruen.
3. Golden Regression mit `SimulationData_Breitenerhebung.csv` ist gruen.
4. `scripts\regression_csv_golden.py` meldet `differences=0`.
5. Der DIBS-Core hat weiterhin keine Django-/GraphQL-Abhaengigkeit.
6. DataSourceCSV und DataSourceDjango bleiben kompatibel, weil der Core den
   stateful DataSource-Vertrag beibehaelt.

Verwendete Abschlussbefehle:

```powershell
python -m pytest -q -p no:cacheprovider tests\error_handling
python -m pytest -q -p no:cacheprovider tests\building_simulator
python scripts\regression_csv_golden.py
```

Ergebnis:

```text
Error-Handling: gruen
Building-Simulator: gruen
Golden Regression: differences=0
```

Bewertung:

Die Error-Handling-Migration ist fachlich abgeschlossen. Gueltige Simulationen
liefern weiterhin dieselben Golden-Ergebnisse. Fehlerpfade sind typisiert und
koennen von Host-Anwendungen wie Lezbau ueber `DIBSError.code`, `phase` und
`context` ausgewertet werden.

## 12. Testmatrix

| Szenario | Erwartetes Verhalten |
|---|---|
| Gueltiges Gebaeude | identisches Ergebnis wie Baseline |
| Fehlende PLZ | `PLZNotFoundError` |
| Unbekannte HK/UK | `HkOrUkNotFoundError` |
| Fehlende Nutzungszeit | `UsageTimeError` |
| Unbekanntes Heizsystem | `UnsupportedSystemError` |
| Unbekanntes Kuehlsystem | `UnsupportedSystemError` |
| Ungueltiger RC-Zustand | `SimulationStateError` oder `ThermalCalculationError` |
| Optionales Numba fehlt | Warning, Python-Fallback |
| Fehler in Einzelgebaeude | Exception erreicht Host |
| Fehler in Batch | explizites Fehlerresultat je Gebaeude |

## 13. Empfohlene Reihenfolge

```text
D-EH1 Tests fuer Ist-Verhalten
  -> D-EH2 Basisklasse
  -> D-EH3 Konstruktoren
  -> D-EH4 print-and-swallow
  -> D-EH5 Built-in-Exceptions
  -> D-EH6 DataSource-Vertrag
  -> D-EH7 oeffentliche DIBS-Grenze
  -> D-EH8 Logging
  -> D-EH9 Lezbau-Vertrag
  -> D-EH10 Regression und Performance
```

Nach jedem Schritt werden Tests ausgefuehrt und die gueltigen
Simulationsergebnisse mit der Baseline verglichen.

## 14. Git-Strategie

Der Performance-Stand auf `dibscc_opt` soll vor Beginn sauber committed und
gepusht sein. Error Handling soll mindestens in eigenen Commits umgesetzt
werden. Ein eigener Branch ist empfohlen, aber nicht technisch erforderlich.

Empfohlene Commits:

```text
test(errors): capture current DIBS failure behavior
refactor(errors): introduce common DIBSError hierarchy
fix(errors): propagate building and GHG failures
refactor(errors): type simulation and datasource failures
test(errors): cover public DIBS error contract
```

## 15. Nicht-Ziele

Die DIBS-Fehlermigration soll nicht:

1. GraphQL oder Django in DIBS einfuehren.
2. Frontendtexte in DIBS festlegen.
3. gueltige Simulationsergebnisse veraendern.
4. Fehler stillschweigend ignorieren.
5. jede interne Exception in `DIBSError` umwandeln.
6. Performance- und Error-Handling-Aenderungen im selben Commit vermischen.

## 16. Definition of Done

Die DIBS-Fehlerbehandlung ist abgeschlossen, wenn:

1. alle erwarteten DIBS-Fehler von `DIBSError` erben,
2. alle Fehler einen stabilen Code besitzen,
3. kein fachlicher Fehler mit `print()` verschluckt wird,
4. Methoden entweder gueltige Werte liefern oder Exceptions ausloesen,
5. DataSource-Signaturen nur Erfolgswerte als Rueckgabetyp enthalten,
6. Einzel- und Batchverhalten definiert und getestet sind,
7. Lezbau DIBS-Fehler zentral adaptieren kann,
8. gueltige Stunden- und Summary-Ergebnisse unveraendert bleiben,
9. der fehlerfreie Pfad keinen relevanten Performanceverlust zeigt,
10. der Fehlervertrag dokumentiert und durch Tests abgesichert ist.



