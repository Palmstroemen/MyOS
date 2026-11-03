# Demo in drei Minuten

Das Drehbuch für eine kurze Vorführung von MyOS, live oder als Video. Stand 3. November 2026.
Es zeigt nur, was heute funktioniert. Aus derselben Geschichte entstehen später der Schnellstart
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

**Demo-Daten** (ein eigener Projekte-Ordner, nicht der Alltag):
- `Downloads` mit etwa 30 gemischten Dateien: Rechnungen als PDF, Fotos, ein Vertrag, Notizen.
- `Projekte/Urlaub 2025`: ein gewöhnlicher Ordner, noch kein Projekt, mit fünf Dateien, darunter
  eine Hotelrechnung und zwei Fotos.
- `Projekte/Familie`, `Projekte/Job`, `Projekte/Auto`: Projekte, deren `04_Finanz` schon ein paar
  Rechnungen hält, damit die Brille etwas zu zeigen hat.
- `Projekte/Wohnen`: ein Projekt ohne `04_Finanz`.
- In LibreOffice offen und noch nicht gespeichert: `Rechnung Heizung 2025.odt`.

**Zustand vor dem Start:**
- Scope läuft im Projekte-Ordner, keine Brille auf.
- Das Laufwerk „Perspektiven“ liegt neben `Projekte` (Scope startet es).
- Die FilesPanel-Ansicht zeigt große Symbole, die blassen Ordner oben.
- Nemo steht in `Projekte/Urlaub 2025`.

## Die Szenen

### 1. Das Durcheinander (0:00–0:20)

- **Bild:** Nemo zeigt `Downloads`, langsam nach unten gescrollt.
- **Handgriff:** nur scrollen.
- **Text:** „Steuererklärung. Irgendwo hier sind die Rechnungen von 2025. Und in den Mails. Und
  auf dem Desktop. Jeder kennt das.“

### 2. Ordner, die warten (0:20–0:45)

- **Bild:** Scope zeigt `Urlaub 2025`, ein gewöhnlicher Ordner mit fünf Dateien.
- **Handgriff:** den Ordner auswählen, auf **P** klicken („zum Projekt machen“).
- **Was passiert:** Oben erscheinen blasse Standardordner: `01_Info`, `04_Finanz`,
  `08_Dokumentation` und weitere. Rechts in Nemo ändert sich nichts.
- **Text:** „Jetzt ist es ein Projekt. Siehst du die blassen Ordner? Die gibt es noch nicht. Rechts,
  im gewöhnlichen Dateibrowser, ist nichts passiert. Sie warten nur.“

### 3. Ein Ordner wird geboren (0:45–1:20)

- **Handgriff:** die Hotelrechnung auf den blassen Ordner `04_Finanz` ziehen.
- **Was passiert:** Links wird `04_Finanz` kräftig, rechts in Nemo taucht er auf, mit der
  Rechnung darin.
- **Handgriff:** die zwei Fotos auf `08_Dokumentation` ziehen. Derselbe Effekt.
- **Text:** „Ich habe keinen Ordner angelegt. Er ist da, wenn ich ihn brauche. Und er heißt in
  jedem Projekt gleich: `04_Finanz`. Das versteht auch der Computer, ganz ohne KI.“

### 4. Die Brille (1:20–2:00)

- **Handgriff:** in Scope zu `Familie` wechseln, Doppelklick auf `04_Finanz`.
- **Was passiert:** Die Pfadleiste zeigt den Rahmen `Familie › [✕ 04_Finanz]`, das FilesPanel die
  Rechnungen der Familie.
- **Handgriff:** in der Projektzeile Doppelklick auf `Job`, dann auf `Auto`.
- **Was passiert:** Die Brille geht mit. Man bleibt in den Finanzen und wechselt nur das Projekt.
- **Text:** „Das ist die Brille des Buchhalters. Ich bleibe in den Finanzen und gehe durch meine
  Projekte.“
- **Handgriff:** in Nemo zu `Perspektiven/04_Finanz/Projekte` gehen.
- **Was passiert:** Familie, Job, Auto und Urlaub 2025 liegen nebeneinander, jeweils nur mit ihren
  Finanzen.
- **Text:** „Und so sieht es jedes Programm: alle Rechnungen, nach Projekten sortiert. Ich musste
  die Projekte nirgends ein zweites Mal anlegen.“

### 5. Jedes Programm kann es (2:00–2:40)

- **Handgriff:** in LibreOffice „Speichern unter“, dann `Perspektiven/04_Finanz/Projekte/Wohnen`
  wählen und speichern.
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
- **Die blassen Ordner stehen nicht oben:** Die Rasteransicht übernimmt noch die Sortierung der
  Listenansicht (Logbuch). Vorher in der Listenansicht nach Namen sortieren.

## Für die Videofassung

- **Untertitel:** Der Text steht als Untertitel im Bild, die Stimme ist optional.
- **Zoom:** Bei der Geburt (Szene 3) und beim Rahmen in der Pfadleiste (Szene 4) kurz zoomen.
- **Schnitte:** Zwischen den Szenen schneiden statt warten, dann bleibt es unter drei Minuten.
