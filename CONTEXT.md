# CONTEXT.md

## Projektkern

DIBS Computing Core ist eine Python-Bibliothek fuer die stuendliche
Energiesimulation deutscher Nichtwohngebaeude nach dem vereinfachten
5R1C-Verfahren der ISO 13790:2008.

Die Bibliothek berechnet Heiz- und Kuehlbedarf, Warmwasser, Strom,
Systemenergien, Primaerenergie, Treibhausgasemissionen sowie stuendliche und
aggregierte Ergebnisse.

## Zielgruppe

Das Package richtet sich an Entwickler, wissenschaftlich-technische Anwender
und Backend-Systeme wie Lezbau. Es ist keine eigenstaendige Endnutzer-App und
besitzt keinen eigenen Webserver oder Frontend-Code.

## Integration

Eine Host-Anwendung implementiert `DataSource` und liefert vorbereitete
Gebaeude-, Wetter-, Profil- und Faktordaten:

```text
Host / Lezbau
  -> DataSource
  -> DIBS.calculate_result_of_one_building()
  -> 8760-Stunden-Simulation
  -> Result + SummaryResult
```

Django, Datenbankmodelle, GraphQL, HTTP, Authentifizierung und Frontendtexte
bleiben ausserhalb des Computing Core.

## Aktueller Stand

- Python `>=3.10`, `src/`-Layout und Flit-Core-Build.
- pytest-Tests und Black-Konfiguration mit 88 Zeichen.
- Serielle 8760-Stunden-Zustandsfortschreibung je Gebaeude.
- Gebaeudeweise Multiprocessing-Unterstuetzung.
- Vorallozierte Resultatlisten und optionaler Numba-Thermalkern.
- Typisierte `DIBSError`-Hierarchie mit `code`, `phase` und `context`.
- Fehlerweitergabe und Phasenzuordnung fuer Einzelgebaeude.
- Kein aktives `print()` und keine globale Logging-Konfiguration im Core.

## Aktuelle Entwicklungsrichtung

Der Schwerpunkt liegt auf einem stabilen Fehlervertrag zwischen DIBS und der
Host-Anwendung. Fuer Einzelgebaeude sind Fehlerhierarchie, Weitergabe,
DataSource-Typen und Logging-Regeln umgesetzt.

Noch offen sind:

- Batch-/Multiprocessing-Fehler und Partial Results,
- Lezbau-Integration des DIBS-Fehlervertrags,
- Golden-Snapshot- und Performance-Regression,
- spaetere Entfernung temporaerer `SIM_PERF`-Messungen.

## Leitplanken

- Fachliche Ergebnisgleichheit hat Vorrang vor Performance.
- Formelaenderungen benoetigen feste Inputs und Ergebnisvergleich.
- Datenzugriff bleibt hinter `DataSource`.
- API-spezifische Fehler entstehen im Host, nicht in DIBS.
- Stunden eines Gebaeudes sind thermisch voneinander abhaengig.

Weitere Informationen:

- [`AGENTS.md`](AGENTS.md): Arbeitsregeln und Befehle
- [`ARCHITECTURE.md`](ARCHITECTURE.md): Komponenten und Datenfluss
- `docs/error_handling/`: Fehlermigrationsplan
