# Demo in drei Minuten

Das Drehbuch für eine kurze Vorführung von MyOS, live oder als Video. Stand 3. November 2026.
Es zeigt nur, was heute funktioniert; am 3. November einmal ganz durchgespielt (Xephyr, mit den
Daten aus `scripts/make_demo_data.py`). Aus derselben Geschichte entstehen später der Schnellstart
vor dem Kurs und die Methode auf einer Seite ([Roadmap](../Roadmap.md)).

## Worum es geht

**Der eine Satz:** Ordner, die erst entstehen, wenn du sie brauchst – und eine Brille, durch die
du alle Projekte auf einmal siehst.

**Der Aufhänger:** die Steuererklärung. „Wo sind alle Rechnungen von 2025?“

**Für wen:** Menschen, die ihre Ablage kennen und nicht mögen, vom Haushalt bis zum kleinen
Betrieb. Keine Vorkenntnisse.

**Die Wörter:** blasse Ordner (nicht „Embryos“), Standardordner, Brille. „Perspektive“ nur
einmal, beim Laufwerk, weil es so heißt.

## Vorbereitung

**Bildschirm:** links Scope, rechts Nemo, nebeneinander. Rechts ist „die Vergangenheit“, links
„die Zukunft“; dieses Bild trägt die ganze Demo.

**Demo-Daten** (ein eigener Ordner, nicht der Alltag), vor jeder Vorführung frisch:

    python3 scripts/make_demo_data.py ~/Demo

Ein kurzer Pfad: Scope zeigt die Pfadleiste ab `/`, bei einem langen Pfad rutschen die Projekte
aus dem Bild. Das Skript baut neu, wo schon eine Demo lag, und lässt jeden anderen Ordner in Ruhe.
Darin:
- `Downloads` mit etwa 30 gemischten Dateien: Rechnungen als PDF, Fotos, ein Vertrag, Notizen.
- `Projekte/Urlaub 2025`: ein gewöhnlicher Ordner, noch kein Projekt, mit fünf Dateien, darunter
  eine Hotelrechnung und zwei Fotos.
- `Projekte/Familie`, `Projekte/Job`, `Projekte/Auto`: Projekte, deren `04_Finanz` schon ein paar
  Rechnungen hält, damit die Brille etwas zu zeigen hat.
- `Projekte/Wohnen`: ein Projekt ohne `04_Finanz`.
- `Downloads/Rechnung Heizung 2025.odt`, in LibreOffice geöffnet.
- `Projekte/.MyOS/Templates/Standard`: die Vorlage, ohne Zugriffsrechte (sonst zeigt Scope links ein
  Zugriffs-Panel und sperrt Aktionen).

**Zustand vor dem Start:**
- Scope läuft in `~/Demo/Projekte`, keine Brille auf. Das Laufwerk „Perspektiven“ liegt dann
  neben `Projekte`; Nemo und der Speichern-Dialog von LibreOffice führen es unter „Geräte“.
- In Scope eingestellt: die Projektzeile an (⚙ → Scope), im Dateibereich Ordner an und
  Röntgenansicht aus (Knöpfe rechts). Mit Röntgen zeigt Scope statt `Urlaub 2025` dessen Dateien.
- Nemo steht in `Downloads`.

## Die Szenen

### 1. Das Durcheinander (0:00–0:20)

- **Bild:** Nemo zeigt `Downloads`, langsam nach unten gescrollt.
- **Handgriff:** nur scrollen.
- **Text:** „Steuererklärung. Irgendwo hier sind die Rechnungen von 2025. Und in den Mails. Und
  auf dem Desktop. Jeder kennt das.“

### 2. Ordner, die warten (0:20–0:45)

- **Bild:** Scope zeigt `Projekte`: Auto, Familie, Job, Wohnen mit P, dazu `Urlaub 2025` ohne.
  Nemo wechselt nach `Projekte/Urlaub 2025`: fünf Dateien.
- **Handgriff:** `Urlaub 2025` auswählen, auf **P** klicken („zum Projekt machen“; auch per
  Rechtsklick). Dann Doppelklick hinein.
- **Was passiert:** Der Ordner bekommt sein P. Drinnen stehen oben blasse Standardordner:
  `01_Info`, `04_Finanz`, `08_Dokumentation` und weitere. Rechts in Nemo ändert sich nichts.
- **Text:** „Jetzt ist es ein Projekt. Siehst du die blassen Ordner? Die gibt es noch nicht. Rechts,
  im gewöhnlichen Dateibrowser, ist nichts passiert. Sie warten nur.“

### 3. Ein Ordner wird geboren (0:45–1:20)

- **Handgriff:** die Hotelrechnung auf den blassen Ordner `04_Finanz` ziehen.
- **Was passiert:** Links wird `04_Finanz` kräftig, rechts in Nemo taucht er auf, mit der
  Rechnung darin.
- **Handgriff:** das Strandfoto auf `08_Dokumentation` ziehen. Derselbe Effekt.
- **Text:** „Ich habe keinen Ordner angelegt. Er ist da, wenn ich ihn brauche. Und er heißt in
  jedem Projekt gleich: `04_Finanz`. Das versteht auch der Computer, ganz ohne KI.“

### 4. Die Brille (1:20–2:00)

- **Handgriff:** in Scope zu `Familie` wechseln, in der MyOS-Zeile Doppelklick auf `04_Finanz`.
- **Was passiert:** Die Pfadleiste zeigt den Rahmen `Familie [✕ 04_Finanz]`, Scope wird grau
  (der Desk der Finanzabteilung), der Dateibereich zeigt Ausgaben und Einnahmen der Familie.
- **Handgriff:** in der Projektzeile Doppelklick auf `Projekte`, dann auf `Job`.
- **Was passiert:** Die Brille geht mit: `Job [✕ 04_Finanz]`. Auf `Projekte` dazwischen ist der
  Rahmen kurz weg (das Regal kommt mit E4); nicht kommentieren, gleich weiter.
  Achtung: Ein Doppelklick auf ein Projekt im *Dateibereich* nimmt die Brille ab.
- **Text:** „Das ist die Brille des Buchhalters. Ich bleibe in den Finanzen und gehe durch meine
  Projekte.“
- **Handgriff:** in Nemo zu `Perspektiven/04_Finanz/Projekte` gehen.
- **Was passiert:** Auto, Familie, Job, Urlaub 2025 und Wohnen liegen nebeneinander, darin nur
  ihre Finanzen. Wohnen nicht öffnen: Ohne `04_Finanz` zeigt das Laufwerk dort das Projekt
  selbst, mit Grundriss und Notizen.
- **Text:** „Und so sieht es jedes Programm: alle Rechnungen, nach Projekten sortiert. Ich musste
  die Projekte nirgends ein zweites Mal anlegen.“

### 5. Jedes Programm kann es (2:00–2:40)

- **Handgriff:** in LibreOffice „Speichern unter“, links „Perspektiven“, dann `04_Finanz`,
  `Projekte`, `Wohnen` und speichern.
- **Was passiert:** In Scope (oder Nemo) unter `Projekte/Wohnen` ist `04_Finanz` neu geboren, die
  Rechnung liegt darin.
- **Text:** „LibreOffice weiß nichts von MyOS. Ich habe nur den Weg über die Finanzen genommen. Die
  Rechnung liegt trotzdem im Projekt Wohnen, und der Ordner dafür ist eben entstanden.“

### 6. Alles beim Projekt (2:40–3:00)

- **Bild:** Nemo zeigt `Projekte/Urlaub 2025`: `04_Finanz`, `08_Dokumentation`, die übrigen
  Dateien.
- **Text:** „Alles vom Urlaub liegt beim Urlaub. Auf einen USB-Stick kopiert, hat der andere alles
  und findet sich sofort zurecht. Und trotzdem habe ich den Überblick über alle Rechnungen.“
- **Schluss:** „Ordner, die entstehen, wenn du sie brauchst. Und eine Brille für alle Projekte.
  Das ist MyOS.“

## Was nicht vorkommt

Es kommt nicht vor, weil es ablenkt oder noch nicht fertig ist:
- **Suche über alle Projekte mit der Brille:** noch nicht gebaut (E7).
- **Das Regal in Scope** (Projekte zur Brille auswählen): kommt mit E4. Darum wechselt die Demo
  die Projekte über die Projektzeile.
- **Mailprogramme, die selbst ablegen, und die lokale KI:** Zukunft. Höchstens als Ausblick nach
  der Demo, klar als solcher benannt.
- **Tags, Zugriffsrechte, Filter, Desk, SunTree:** gut, aber für die zweite Begegnung.
- **Das Energie-Argument:** erst mit Messung.

## Was schiefgehen kann

- **Ein Doppelklick wird ein Einfachklick:** In der Projektzeile wechselt ein einfacher Klick nur die
  Ansicht. Vorher üben, sonst wirkt die Brille unzuverlässig.
- **Das Laufwerk fehlt in Nemo:** Scope wurde nach Nemo neu gestartet. Nemo einmal neu laden.
- **Nach der Demo hängt das Laufwerk noch:** Solange LibreOffice die Datei offen hat, bleibt es
  eingehängt. LibreOffice zuerst schließen.
- **Zwei Laufwerke „Perspektiven“:** Läuft daneben ein Scope auf anderen Projekten, haben Nemo und
  LibreOffice zwei davon. Für die Vorführung nur das Demo-Scope laufen lassen.
- **Scope beenden:** über das Fenster. Ein von außen beendetes Scope (SIGTERM) lässt das Laufwerk
  stehen.

## Für die Videofassung

- **Untertitel:** Der Text steht als Untertitel im Bild, die Stimme ist optional.
- **Zoom:** Bei der Geburt (Szene 3) und beim Rahmen in der Pfadleiste (Szene 4) kurz zoomen.
- **Schnitte:** Zwischen den Szenen schneiden statt warten, dann bleibt es unter drei Minuten.
