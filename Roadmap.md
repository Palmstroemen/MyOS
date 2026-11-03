# MyOS Roadmap

Stand 3. November 2026. Die strategische Roadmap; die laufenden Aufgaben stehen im
[ProjectLogbook.md](ProjectLogbook.md). Auch als Seite:
[MyOS Roadmap](https://claude.ai/artifact/FMe7ZFHdAruBYHkzSacKUr).

Die Idee trägt, und durch KI ist sie eher aktueller geworden. Scheitern würde MyOS nicht am
Denken, sondern an der Verbreitung und an zu vielen Funktionen auf einmal. Diese Roadmap leitet
sich daraus ab, was frühere Versuche gelehrt haben.

Entstanden aus der Rückmeldung einer Prokuristin eines Fenstertausch-Betriebs („So arbeitet doch
keiner", sie kannte nur ihre 15 Jahre alte Access-Datenbank) und dem Vergleich mit früheren
Versuchen, die Ablage neu zu denken.

## 00_Admin – Die Leitfrage

**Benutzt jemand MyOS nach einer Woche freiwillig weiter?**

Nicht „gefällt es?", sondern „bleibt es?". Jeder Schritt unten muss sich daran messen lassen. Die
ersten Antworten kommen vom Testrechner ([docs/TEST-MACHINE.md](docs/TEST-MACHINE.md)).

## 01_Info – Was die Vorläufer lehren

1. **Nicht von anderen abhängen.** OpenDoc und WinFS brauchten, dass alle mitziehen. MyOS muss
   mit unveränderten Programmen heute Nutzen stiften und die Brücken selbst bauen.
2. **Nutzen sichtbar machen.** KDE Nepomuk war mächtig, aber unsichtbar, und wurde abgeschaltet.
   Der Wert muss in den ersten fünf Minuten sichtbar sein.
3. **Mit einer Sache anfangen.** WinFS wollte alles auf einmal. BeOS, Obsidian und Access begannen
   mit einer Sache, die sofort funktionierte.
4. **Methode vor Software.** PARA und Johnny.Decimal verbreiten sich ohne Programm, mit einer
   Seite Erklärung.
5. **Firmen-Apps auf gemeinsamer Datenbasis.** Lotus Notes hat das 30 Jahre bewiesen und starb an
   Oberfläche und Herstellerbindung, nicht am Prinzip.
6. **Eine Gemeinschaft braucht es.** Obsidian lebt von Plugins, Notion von seiner
   Vorlagen-Galerie. Ein Paradigma braucht andere, die darauf bauen.
7. **Standards statt eigener Formate.** vCard, iCalendar, ebInterface, Maildir, Seitendateien für
   Tags: übernehmen, wo es sie gibt.
8. **KI als Chance, nicht als Gegner.** Recall zeigt „keine Ordnung, alles durchsuchen" und den
   Datenschutz-Aufschrei dazu. MyOS besetzt die Gegenposition: Ordnung, lokal, eine KI, die ablegt.

## 07_Arbeit – Die Roadmap

Ohne Termine: Die Reihenfolge ist die Information. In Klammern steht, aus welcher Lehre ein
Schritt folgt.

### Jetzt – Beweisen, dass es bleibt

- **Testrechner auswerten** (Leitfrage). Kommentare und Änderungen der Testerinnen und Tester
  sammeln und lesen, Muster suchen: Wo steigen sie aus, was begeistert?
- **Ein Einstiegsfall: der kleine Betrieb** (3). Vom Fenstertausch-Beispiel her die fünf häufigsten
  Tätigkeiten der Prokuristin als kleiner Prototyp in MyOS:
  - Kunde anlegen
  - Rechnung mit fortlaufender Nummer als PDF
  - offene Rechnungen sehen (Perspektive über alle Kunden, Tag `#offen`)
  - Mahnung auslösen
  - die fünfte Tätigkeit, die sie nennt
- **Die Methode auf einer Seite** (4). Projekte, nummerierte Standardordner, Vorschläge und
  Perspektiven so erklärt, dass man sie auch ohne die Software anwenden kann. Das Tutorial bleibt
  die ausführliche Fassung.

### Als Nächstes – Dorthin, wo die Leute schon sind

- **Plattform-unabhängiger Kern** (1). Methode, Dateiformat und Schema laufen auf jedem System.
  Scope, SunTree und PostFix sind die Linux-Oberfläche dazu, nicht die Voraussetzung.
- **Einnisten statt ersetzen** (6). Ein Obsidian-Plugin oder eine Dateimanager-Erweiterung bringt
  Standardordner, Vorschläge und Perspektiven zu den Leuten, ohne Systemwechsel.
- **Brücken selbst bauen** (1). Nicht auf Hersteller warten, sondern importieren: Mails ins
  Projekt, Fotos nach `08_Dokumentation`, Access-Datenbanken für Firmen (wer seine 15 Jahre
  mitnehmen kann, steigt um).
- **Standards übernehmen** (7). Tags für jede Datei per Seitendatei (wie TagSpaces), Kontakte als
  vCard, Rechnungen exportierbar als ebInterface.
- **Sichtbarer Nutzen zuerst** (2). Vorschläge und Perspektiven sind der erste Eindruck. Linse,
  Desk und Perspektiven-Laufwerk bleiben für Fortgeschrittene im Hintergrund. Installation mit
  einem einzigen Schritt.
- **Editieren wie in Obsidian** (2). PostFix bekommt CodeMirror 6 mit Live-Vorschau. Recherchiert,
  erst ein Prototyp im direkten Vergleich mit Obsidian.

### Später – Das Fundament für Firmen und KI

- **Datenbank-Grundfunktionen im Kern** (5). Offenes Datenschema für Kunden, Angebote und
  Rechnungen, lückenlose Nummernkreise, schnelle Abfragen über einen jederzeit neu aufbaubaren
  Index, Archiv und Export. Die Dateien bleiben die Wahrheit, die Oberflächen darüber sind
  austauschbar.
- **Lokale KI als Ablage-Helfer** (8). Eine lokale KI legt ein: Rechnung kommt herein, landet im
  richtigen Projekt unter `04_Finanz`, sichtbar in der Perspektive. Dazu eine Schnittstelle, über
  die Agenten die Struktur lesen und befüllen.

## 08_Dokumentation – Die Vorläufer im Vergleich

Aus dem Wissen, ohne neue Recherche; Jahreszahlen ungefähr.

| Versuch | Idee | Stärke | Woran es lag | Für MyOS |
|---|---|---|---|---|
| BeOS-Dateisystem (ca. 1996) | Dateien mit Attributen, live Abfragen; jede Mail eine Datei mit Feldern | Schnell, echt im Betriebssystem | Plattform starb am Markt | Messlatte für Abfragen im Dateisystem |
| Lifestreams (ca. 1996) | Keine Ordner, ein Zeitstrom | Keine Ablage-Arbeit | Kein Zusammenhang, kein Projektbezug | Gegenentwurf |
| Apple OpenDoc (1990er) | Dokument statt Programm | Konsequent dokumentzentriert | Brauchte alle Entwickler | Gleiches Risiko bei „Programme legen ins Projekt ab" |
| Lotus Notes (ab 1989) | Dokument-Datenbank, Workflows, Rechte, Offline-Abgleich | Jahrzehntelang Rückgrat in Firmen | Sperrige Oberfläche, Herstellerbindung | Am nächsten an der Firmen-Idee |
| Access, FileMaker | Datenbank zum Selbstbauen | Erledigt die Arbeit | Bindung an Hersteller und Format | Was Betriebe heute kennen |
| Microsoft WinFS (2003–2006) | Datenbank unter dem Dateisystem | Durchdacht, ehrgeizig | Zu groß, zu langsam, eingestellt | Warnung: nicht alles auf einmal |
| Haystack, KDE Nepomuk (2000er–2014) | Semantischer Desktop | Mächtige Verknüpfungen | Ressourcenhunger, unsichtbarer Nutzen | Warnung vor Komplexität |
| Windows-Bibliotheken, macOS-Tags | Gespeicherte Suchen, Farb-Tags | Eingebaut | Kaum entdeckt, keine Konventionen | Filter und Tags brauchen Konventionen |
| Smartphones | Jede App hält ihre Daten | Bequem, Massenerfolg | Datensilos, Bindung | Wogegen MyOS antritt |
| Plan 9 | Jeder Prozess hat seine Sicht auf den Baum | Elegant | Nische | Verwandt mit den Perspektiven |
| TagSpaces, TMSU | Tags für jede Datei per Seitendatei | Funktioniert überall | Nische | Lösung für Tags auf PDFs und Fotos |
| PARA, Johnny.Decimal, GTD | Methoden | Ohne Software, eine Seite, Gemeinde | Lebt von Disziplin | Nähe zu den nummerierten Standardordnern |
| Notion | Seiten und Datenbanken, Vorlagen | Einstieg, Vorlagen-Galerie | Cloud, Bindung | Vorbild für den Einstieg |
| Obsidian | Lokale Markdown-Dateien, Plugins | Daten gehören dir, große Gemeinde | Kaum für Firmenprozesse | Technisch am nächsten |
| Solid | Persönlicher Datenspeicher, Apps austauschbar | Das Austausch-Argument | Schwerfällige Standards, wenige Apps | Gleiches Versprechen, einfacher halten |
| Microsoft Recall, Rewind | Alles aufzeichnen, per KI durchsuchen | Kein Aufwand | Datenschutz, keine Struktur | KI-Gegenentwurf |

### Was andere besser machen

- **Notion:** der Einstieg. Eine Vorlage aus der Galerie, in einer Minute produktiv.
- **Obsidian:** Plugins und „deine Dateien, für immer", auf jedem System.
- **Johnny.Decimal:** Erklärbarkeit. Ein Prinzip, eine Webseite.
- **BeOS:** Abfragen direkt im Dateisystem, schnell und überall gleich.
- **Lotus Notes:** Offline-Abgleich und Rechte pro Dokument im Firmenalltag.
- **TagSpaces:** Tags für jede Datei über Seitendateien, bereits erprobt.
