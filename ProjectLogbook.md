---
window_width_px: 900
window_height_px: 650
window_x_permille: 78
window_y_permille: 44
background_color: '#f48fb1'
note_style: notebook
---
# 📖 MyOS: IDEAS / TODO / LEARNINGS

---

## 📌 Projektstatus

**Stand:** 2026-10-18  
**Aktuelle Phase:** MVP-Umsetzung mit Fokus auf stabile Kernflows

Der Stand ist deutlich weiter als frühe Prototypenphase.  
Wesentliche Kernbausteine (PostFix, Scope, Tagging, DnD, Thumbnailing, Filter, Perspektiven-MVP mit Daemon, Desk, Sort) sind implementiert und iterativ gehärtet.
Kompakter Überblick: `docs/STATUS.md`.

---

## 🚀 Aktuelle Prioritäten (Roadmap)

Die strategische Richtung (Lehren aus früheren Versuchen, Jetzt / Als Nächstes / Später) steht in
[Roadmap.md](Roadmap.md); hier die laufenden Aufgaben.


[x] Jahresfilter: /Jahr/Monat/-Ablage automatisch (core/filing.py, Designdocument Sort.md):
    Regel im Ordner selbst, flach → virtuell → echt ab NewLevelFrom, Ablage durch Nachholen statt Beobachter, echtes EXIF
    [ ] Regel bequem einrichten (der Knopf "Enable sorting" ist mit der oberen Leiste weg, 2026-10-26: vorerst von Hand); myls zeigt virtuelle Ebenen noch nicht
[ ] SunTree: nur zum Ablegen - zeigt Ordner, keine Dateien, keine Suche (entschieden 2026-10-25)
    [ ] Weiche Krone (SunTree/Designdocument Krone.md, Skizze SunTree/prototype/Krone.html): Feld wächst nach außen,
        ab der Linie T (0,7 R) in den Stamm gesaugt, Zeiger nach innen gezogen; Rückweg ebenso weich
        [x] Schritt 1: Designdokument und Skizze  [x] Schritt 2: Rechnung SunTree/js/Crown.js mit Tests
        [~] Schritt 3: QML mit echten Ordnern (2026-10-25): Krone in einer Canvas, Zeiger gezogen (QCursor.setPos, auch
            beim Drag unter X11 erprobt), Stamm gezeichnet mit Clipboard oben, Klick und Ablegen; offen:
            Feinabstimmung am echten Bildschirm
            [x] Rückweg aus dem Stamm (2026-10-26): Klick auf einen Eltern-Ordner spuckt die Ordner dazwischen aus,
                die Krone läuft zurück, die Einträge im Stamm gleiten
            [x] Halbkreise am Stamm (2026-10-26): Mittelpunkte = Mittelpunkte der Rundungen des CWD-Ovals; Stamm-Knöpfe eckig
            [x] CTD statt CWD in der Mitte (2026-10-26): Klick schaut nur (CTD), Doppelklick setzt das CWD und schließt;
                Brille nur bewusst; das CWD leuchtet, wo es auftaucht (Oval, Stamm, Krone)
            [x] Scope: CWD ebenso leuchtend markiert (2026-10-26): Pfadleiste der Projekte und CWD-Knopf; helles Theme: kräftigerer Rahmen
            [x] Übergang im Stamm (2026-10-26): die Vorschau kommt von oben, das CTD rutscht nach unten, nichts überlappt
            [x] Grenze überholt den Zeiger (2026-10-26): Einsaugen ab 75 % des Feldes bis 25 % in den äußeren Ring
            [x] Immer bereit (2026-10-26): kein X mehr (Strg+Q beendet), Autostart per SunTree/install_autostart.py;
                CWD außerhalb des Projektbaums: an der Projekte-Wurzel
            [x] Hänger beim Tauchen (2026-10-26): Bewegungen von vor dem Setzen des Zeigers warfen die Krone; jetzt bis
                zum Echo des Setzens als Schritte der Hand gezählt
            [ ] Man ist in der Krone gefangen (2026-10-25): loslassen über den Rand auf jeder Ebene, mit einem
                schnellen Ruck oder quer in die andere Hälfte
                -> weitgehend gelöst durch "eine Handlung, dann weg" (2026-10-26); bleibt: Abbrechen (Esc, Shortcut, Klick daneben)
                [x] Seitlich gefangen am ersten und letzten Ordner (2026-10-26): über das Ende hinaus drücken lässt los, auf jeder
                    Ebene (summiert, 0,08 R); die Hälfte greift erst wieder, wenn die Hand sie verlassen hat
            [x] Obere Leiste weg (Filterknöpfe, "Dummy Ablage" - Entwicklungshilfen); das X als Notausgang neben dem Clipboard
            [x] Ohne Hintergrund (2026-10-26): Fenster transparent, nur Krone und Stamm; Klick daneben versteckt SunTree (Abbrechen)
            [x] Panel hinter dem Stamm (2026-10-26): unscharf (etwa 10 px) und schwarz getönt; Momentaufnahme vor dem
                Erscheinen, da Muffin kein Blur-Behind kennt
    [ ] Eine Handlung, dann weg (2026-10-26, Designdokument Krone): Ablegen, CWD, Brille, Clipboard, Ordner in Scope öffnen;
        danach schließt SunTree; Hinweis mit Rückgängig; erscheint mit dem Stamm unter dem Zeiger
        [x] Nach der Handlung weg (2026-10-26): Ablegen, Doppelklick (hinein und weg), Brille auf/ab; Hinweis unten
            mit Rückgängig (auch nach Jahresfilter, geleerte Ordner werden wieder geboren)
        [x] Erscheint mit dem Stamm unter dem Zeiger (2026-10-26); am Bildschirmrand ganz sichtbar, der Zeiger fährt in den Stamm (350 ms), erst dann
            erscheint SunTree; beim Verschwinden fährt der Zeiger zurück, wo er abgeholt wurde
        [x] Sanft weg (2026-10-26): Momentaufnahme zerläuft in Unschärfe, blendet aus und zieht sich zum Stamm
            zusammen (300 ms); ruckelte, weil die Krone den zurückfahrenden Zeiger wieder einfing
        [x] SunTree übersetzt (2026-10-26): SunTree/i18n/suntree_de.ts wie bei Scope, scripts/update_translations.py suntree
        [x] Shortcut während eines Drags kommt an (Xephyr, GTK 3 wie Nemo; Root-Grab und XRecord) - unter Cinnamon noch nicht erprobt
        [x] Globaler Shortcut repariert (2026-10-26): pynput installiert, Vorgabe "<ctrl>+<alt>+<space>" (vorher ungültig, Dienst schlug still fehl)
[ ] Perspektiven (Brille): Verhalten festgelegt (Designdocument Perspective Resolver MVP.md, Teil A, 2026-10-22);
    Umsetzung: eine Sitzung im Daemon, FUSE zeigt den ganzen umgedrehten Baum, QML/SunTree ohne eigenen Pfadbau
    [x] E1 Sitzung im Kern  [x] E2 Laufwerk "Perspektiven" + Daemon  [x] E3 Scope an der Sitzung  [x] E3b Pfadleiste mit Rahmen (CLD)  [x] E3c Desk der Abteilung (Template gewinnt, Änderungen ins Template)
        [ ] E4 Minimalansicht M mit Pfad-Dropdown (Hover), Regal = Projekte einer Ebene nach rechts
            Demo (2026-11-03): heute geht die Brille nur über die Projektzeile mit, zwei Doppelklicks
            ("Projekte", dann das Projekt), dazwischen ist der Rahmen weg; ein Doppelklick auf ein Projekt im
            Dateibereich nimmt sie ab
            [x] Schritt 1: Knopf M, eine Zeile, Dropdown bis "Projekte", Kaskade nach rechts; schmale Knöpfe, 1x Suche und Clipboard
            [x] Clipboard (Multiclipboard, wandert in alle Projekte mit) als kleiner Icon-Knopf: in den Werkzeugen von M
            [x] Werkzeuge von M (2026-10-26): Knopfzeile oben im CWD-Dropdown statt Menü - Clipboard, Suche, Hell/Dunkel,
                Sprache, versteckte Ordner (Scope/CwdTools.qml); M wird ein eigenes, oben angedocktes Werkzeug (kein H, kein E)
            [x] M bleibt eine Zeile (2026-10-26): MyOS-Ordner brechen nicht mehr in eine zweite Zeile um; Mausrad schiebt
            [ ] Setup auf der Rückseite von Scope (Scope/Designdocument Setup.md): ⚙ dreht Scope um; Tabs Allgemein, Scope,
                Headline, SunTree; eine Einstellungsdatei für alle (core/settings.py, ~/.config/MyOS/MyOS.conf)
                [x] Schritt 1 (2026-10-26): Umdrehen, Hell/Dunkel und Sprache (bleiben jetzt gespeichert), SunTree-Werte
                [x] Kleine Krone im SunTree-Tab (2026-10-26): leuchtende Grenzlinien, Tauchgang bei jeder Änderung
                [ ] Schritt 2: Farbschemata wählen
                    [x] Farben umgezogen (2026-11-06): die 34 Farben aus main.qml in core/schemes (dark, light), sieht
                        pixelgleich aus
                    [x] Verstreute Farben aufgeräumt (2026-11-06): Setup-Seite, Auswahl, Ablege-Markierung, Rahmen der
                        Brille, ACL-Dialoge im Schema; Mitte des FilesPanel je Schema einstellbar (filesPanelCenter):
                        war ein 20-%-Schleier über dem Rahmen und über den Dateien, beide Themen landeten bei Mittelgrau
                    [x] Auswahl im Tab Allgemein (2026-11-06): kleines Scope je Schema statt des Knopfs
                    [ ] Drittes Schema; General/colorScheme löst General/darkTheme ab
                    [x] Dialoge bleiben bewusst vertauscht (hell im dunklen Thema): so übersieht man sie nicht (2026-11-06)
                [ ] Schritt 3: bearbeiten
                    [x] SunTree und kleine Krone am Schema (2026-11-06): 31 Farben im Schema, liest es beim Erscheinen; Dunkel wie
                        bisher, Hell neu; Schrift auf Projektfarben kippt, wo sie unlesbar wäre; Hinweis bleibt in beiden dunkel
                    [x] Hintergrund Dateibereich im Setup (2026-11-06): Farbkästchen öffnet die Farbauswahl, je Schema, wirkt sofort, liegt in
                        ~/.config/MyOS/schemes über den mitgelieferten Schemata
                    [ ] Beim Testlauf: Projektfarbe macht 52 % der Mitte aus, Weiß ist so nicht erreichbar; Anteil senken?
                    [x] Farbkästchen ziehen (2026-11-06): rechts heller, links dunkler, oben satter, unten blasser; kein "Standard" daneben
                    [x] Durchgreifen behoben (2026-11-06): Ziehen auf der Rückseite weckte die DragHandler der Vorderseite und
                        erwischte Ordner; die Vorderseite nimmt jetzt nichts an, solange die Rückseite zu sehen ist
                    [x] Elf Farben in vier Gruppen im Setup (2026-11-06), Deckkraft für Auswahl und Ablegen, "Alle Farben
                        zurücksetzen"; Rahmen des FilesPanel hat die Farbe des Reiters; Nebenschriften aus der Schrift berechnet
                    [ ] Eigenes Schema speichern
                [ ] Schritt 4: Tabs Scope und Headline
                [~] Obere Leiste leeren (2026-10-26): Hell/Dunkel, Sprache weg (Allgemein); Zeilen an/aus im Tab Scope;
                    "Dateien 50%", "Projekt mit Thema versehen", "Ordnung aktivieren", "Schmal", Edge-Dock-Schalter entfernt;
                    Filter im Tab Scope; bleiben: ⚙ ganz links und M (eine Zeile per Vorgabe aus: vorerst nicht)
                Später: Anmelden/Ummelden, Abschalten
            [ ] Schritt 2: Auftauchen am oberen Bildschirmrand (Edge-Dock) - zurückgestellt (2026-10-25): im Prototyp reicht
                das CWD links oben im Scope-Fenster. Später voraussichtlich: volle Bildschirmbreite, Kante über die ganze
                Breite klappt sofort auf, zu nach ca. 0,5 s ohne Maus im Fenster; Verhältnis zum alten Edge-Dock offen
            [x] Ein Badge (z. B. das € von 04_Finanz) nimmt Klicks an wie das Ordner-Icon (2026-10-25)
            [ ] Beim visuellen Makeover: Rahmen-Unterkante in der waagrechten Pfadleiste abgeschnitten (H und M);
                in H springt bei sehr langer Pfadzeile das Layout, sobald die Maus auf einen Ordner fährt (die Pfadzeile
                kommt nach oben, die Ordner rutschen weg, ein Doppelklick trifft ein Pfadsegment) - schon vor M so
        [x] E5 SunTree an der Sitzung (2026-10-25): eine Brille mit Scope (daemon/lens_link.py), Gesten wie in Scope,
            Rahmen mit ✕ statt CPD-Stapel
            [x] Brille bleibt auf, bis man sie abnimmt (2026-10-25): ein Ordner ohne Projekt (Job/Aufträge) hält sie im
                Projekt, ein Ordner voller Projekte legt sie aufs Regal; MyOS-Ordner nur links (auch geboren); SunTree
                zeichnet Embryos blass
            [x] Scope und SunTree teilen immer denselben Ort (2026-10-25): beide folgen dem CWD der Sitzung, wenn man
                sich ihnen zuwendet (Scope: Fenster aktiv oder Maus darin; SunTree: Hotkey); nichts läuft im Hintergrund
        [x] E6 Filter (2026-10-25): "## Perspective" nennt die Brille (04_Finanz/Ausgaben); von Hand gewählt setzt der
            Filter sie auf, wo man steht, und nimmt sie beim Aufheben wieder ab (nur solange es noch seine ist); ein
            Auto-Filter nie. Alte CPD-Schicht entfernt (perspective_resolver.py, ScopeApi perspective_*, Teil B)
            Zurückgenommen (2026-10-26): die Wahl von Hand samt Menü (öffnen, speichern) ist weg - die Brille kommt per
            Doppelklick auf den MyOS-Ordner; Auto-Filter bleiben
        [x] Filter in .MyOS/Filters wirken nur noch von Hand (2026-11-06, myfilter), Filter.md weiter von selbst; Name mit Pfad im
            Dateibereich weg, nur beim Flachklopfen der Pfad von hier aus
        [ ] E7 Suche mit Brille über alle Projekte (nur die Abteilungsordner, Spalte "Projekt"; Designdoc A9) -
            zurückgestellt (2026-10-25), bis die Suche im Alltag fehlt; schlank wäre: nur Dateinamen, ein Feld in Scope
    [ ] Laufwerk bleibt eingehängt, wenn Scope von außen beendet wird (SIGTERM; 2026-11-03, Demo): Scope fragt
        den Daemon nur beim Schließen übers Fenster; der Daemon musste selbst beendet werden
    [ ] Laufwerk: ein Projekt ohne Abteilungsordner zeigt unter 04_Finanz/Projekte/<Projekt> das Projekt selbst
        (v1.1-Fallback, damit Speichern dort den Ordner gebiert) - in der Buchhalter-Ansicht sieht man so Grundriss
        und Notizen von Wohnen; besser leer zeigen und trotzdem dorthin speichern lassen? (2026-11-03, Demo)
    [ ] MyOS-Dienst (Konzept A9, 2026-10-23): Laufwerk mit der Anmeldung statt mit Scope; eingehängt wie ein
        Netzlaufwerk unter /run/user/<uid>/myos, neben "Projekte" nur ein Symlink (sonst ist alles doppelt);
        Suchen in der Perspektive (Scope über alle Projekte, Spalte "Projekt"). Vorher bei dir prüfen:
        Nemo, Déjà Dup, Suchindex mit dem Symlink. Entscheiden: vor E3?
    [ ] Energiemessung der Suche (A9): künstlicher Bestand (z. B. 200 Projekte), ganzer Home-Ordner vs. nur
        */04_Finanz vs. Indexabfrage; berührte Dateien, gelesene Bytes, Zeit, Joule (RAPL, /sys/class/powercap).
        Realistisch mit der Struktur echter Projekte (nur Mengen und Größen, keine Namen oder Inhalte)
    [ ] Standardperspektiven nebeneinander (Idee 2026-10-24): einige wenige feste Brillen parallel zeigen
        (Fotos, Videos, Dokumente, ...), wie die Bibliotheken herkömmlicher Systeme; ein leichter Übergang
        für Umsteiger
[ ] ACLs
[ ] Perspektiven (MVP mit Resolver/FUSE/Daemon läuft; Persistenz/Sharing offen)
[ ] Rooms-Konzept (projektabhängige Desktops)
    [x] Desktop folgt den Projekten: Theme, Taskleisten-Theme (PanelTheme), Hintergrund; Änderungen werden automatisch gespeichert
    [ ] Beim Umschalten des Taskleisten-Themes ordnet Cinnamon die Fenster in der Taskleiste neu an (beobachten)
    [x] Taskleisten-Programme pro Projekt (`## Taskbar`; Cinnamon, GNOME)
    [ ] Taskleiste unter KDE; Programmnamen statt .desktop-Kennungen in Scope
[ ] RecentFiles
[ ] Learning MyOS weiter ausbauen
    [x] Tutorial harmonisiert (2026-10-26): Deutsch durchgehend "du", Englisch 1-16, Ordnernamen wie in der Vorlage,
        Übungsdaten (Lektion 4, 5, 7, 10, 11; scripts/make_tutorial_data.py), Übungslinks "▶ Übung öffnen" in PostFix
    [x] Testrechner (2026-10-26, docs/TEST-MACHINE.md): jeder Tester bekommt eine frische Kopie (~/MyOS-Tutorial),
        "💬 Kommentar" unter jeder Lektion, "✅ Bin fertig" in Lektion 16 sammelt Kommentare und Änderungen nach
        ~/MyOS-Testergebnisse, setzt alles zurück und öffnet Lektion 1 (scripts/testrun.py)
    [x] PostFix: Obsidian-artiges Editieren mit CodeMirror 6 in QtWebEngine - recherchiert 2026-10-26, gebaut
        2026-11-03 (ein Editor für alle Zettel, leichte Darstellung), Standard seit 2026-11-07;
        `MYOS_POSTFIX_EDITOR=line` holt den alten Zeileneditor zurück, bis er geht
    [ ] Am Ende des Tutorials (Idee 2026-10-24): Bitte an den Nutzer, selbst eine oder mehrere
        Template-Strukturen zu entwerfen: wie er sie in Firmen vorgefunden hat oder für vernünftig hielte,
        und vielleicht eine andere für sich privat
[ ] Beispielanwendung Zeiterfassung (Idee 2026-10-24): Stunden pro Projekt, keine proprietäre Datenbank,
    sondern kleine MD-Dateien im Projekt selbst (Tabelle: wann, wie lange, optional was); eine Perspektive
    zeigt die Gesamtübersicht als Dateien, ein kleines Programm wertet sie aus. Schwierig: offen gelassen ist
    nicht gearbeitet. Erster Anlauf: Aktivität (Mausbewegungen, Bearbeitungen auch in anderen Programmen)
    mit einer Nachlaufzeit von etwa 5 min zählen
[ ] Demodaten als Playground
[ ] Scope UI verfeinern  
    [x] Röntgenblick (X-Ray): kleine Ordner durchsichtig, solange die Liste ohne Scrollbalken passt; Standard an; auch `myls --roentgen`
    [x] Röntgenblick: eigenes Icon (2026-10-26, Theme/icons/xray.svg: Film mit Brustkorb statt Ordner)
    [x] Dateibereich (2026-10-26): Embryos unter den Ordnern blass (0,4) wie in den Ordnerzeilen - fehlte bisher;
        neuer Ordnertag als blasser Tag ohne Namen am Ende der Tags, ein Klick benennt ihn ("#"-Knopf weg)
        Blässe der Embryos einstellbar - für den Benutzer "Vorgeschlagene MyOS-Ordner" (Setup, Allgemein, Live-Vorschau
        in allen drei Darstellungen; Scope und SunTree); ihre Badges mit eigenem Regler (Vorgabe 70 %); im Menü heißt
        "E Embryos" jetzt "MyOS-Vorschläge"
        Pfadleiste, Vorschau, Vorschau-Hintergrund für beide Browser gleich im Setup (Tab Scope, mit Live-Bildern), aus den
        Anzeige-Menüs heraus; der Projekt-Browser bietet keine MyOS-Vorschläge mehr an (MyOS-Ordner nur links, A3.9)
        Burger-Menüs beider Zeilen ganz ins Setup (Tab Scope): links EIN Beispiel, wie die Zeilen wirklich aussehen, rechts
        Häkchen und Auswahlknöpfe - Zeilen an/aus, Pfadleiste, MyOS-Vorschläge, versteckte Ordner, Vorschau, ihr Hintergrund,
        Ordnerdarstellung je Zeile, Vorschau-Verhalten (sofort wieder öffnen, sanft/ausgewogen/flott); Projekt-Zeile per
        Vorgabe aus (in M bleibt der CWD-Knopf)
        FilesPanel rechts: die Knöpfe sind ihre Icons (knopfgroß, ohne Rahmen: Einstellungen, Ordner, Röntgen, Ansicht,
        Papierkorb); Röntgenbild mit Filmrand, Rippen und Becken; ACL-Chips spiegelbildlich zu den Tags (rund links,
        eckig rechts)
        Ohne Pfadleiste: ↑-Knopf links vom aktuellen Ordner (einen Ordner höher, wie Klick aufs Eltern-Segment; sofort
        bei jedem Klick); M bleibt ohne (dort klettert das CWD-Dropdown); auch im Setup-Beispiel
        M: Lupe aus dem CWD-Dropdown in die Zeile rechts vom CWD geholt (im Dropdown schloss der Klick es, ohne dass das
        Suchfeld zu sehen war); Klick öffnet das Feld mit Fokus, erneuter Klick schließt es
    [x] FilesPanel: Doppelklick auf einen Ordner wechselt noch nicht in diesen Ordner
    [x] P-Button: macht den angewählten Ordner, sonst (ohne Auswahl) den angezeigten zum Projekt; durchgestrichenes P macht ein Projekt wieder zum Ordner; P-Badge auf Projektordnern
    [x] Umbenennen in der Ordnerleiste: Feld zeigt den alten Namen (war leer); F2 benennt die Auswahl im FilesPanel um
    [x] FilesPanel Rasteransicht immer nach Name aufsteigend (oben MyOS-Ordner und Embryos, darunter Unterprojekte
        und andere Ordner, dann Dateien; 2026-11-05); die Spaltensortierung gilt nur noch für die Listenansicht
    [x] FilesPanel: Embryos erscheinen nicht halbtransparent (sollten sie, wie in den Ordnerleisten)
    [x] FilesPanel: blasse Ordner, P und Projektfarben fehlten eine ganze Sitzung, wenn die erste Liste nur Dateien
        hielt (2026-11-03, beim Durchspielen der Demo): jede Zeile trägt jetzt alle Rollen (FormatUtils.listRow)
    [x] FilesPanel: eine Datei senkrecht ziehen scrollte die Liste statt sie zu ziehen (2026-11-05): die Maus
        zieht jetzt nur noch Dateien, gescrollt wird mit Rad und Touch (Flickable.acceptedButtons, ab Qt 6.9)
    [x] FilesPanel: in einer gescrollten Liste wurde die falsche Datei gezogen, die Scrollposition zählte
        doppelt (2026-11-05)
    [x] FilesPanel: der Ordner-Schalter merkt sich seinen Zustand über einen Neustart (2026-11-05)
[ ] PostFix UI verfeinern und Exporter bauen
    [x] ACL-Chip anklicken: Rechte ändern (nur wer `change` hat)
    [x] ACL-Panel: Embryos zählen nicht mit (ein Schalter dafür wird nicht gebraucht)
    [x] Templates mit eigenen ACLs: `.MyOS` der Template-Wurzel (ACLs.md, Desk.md, …) wird in neue Projekte
        kopiert; Rechte der Templates im ACL-Panel sehen und bearbeiten
    [ ] Template-Rechte ausrollen: Abfrage "Sollen diese neuen Rechte auf alle existierenden Projekte
        angewendet werden?" (z. B. wenn ein Mitarbeiter gekündigt wurde)
    [ ] Zugriffsrechte einrichten: als Tutorial/Assistent in 00_Admin (Template-Datei, kommt bei der Geburt mit).
        Nur der Admin richtet Rechte ein; Scope bietet das sonst nirgends an.
        Dafür: Embryos zeigen innen die Dateien ihrer Vorlage blass; eine öffnen = Ordner gebären ("ergreifen").
        Offen: wo das ausgelieferte Standard-Template liegt (Templates/ im Repo ist leer).
    [x] Personen-Chip: Gruppen einer Person ändern (`# Users`)
    [x] Person hinzufügen (neue Zeile in `# Users`; freier Name, Personen des Projekts statt Logins)
    [x] Wer bin ich hier? Eigene Namen pro Rechner in ~/.config/MyOS/Identity.md (core/identity.py)
    [ ] Personen in 00_Admin / 02_Team mit `# Users` verknüpfen (Personenkarten)
    [ ] Authentifizierung; Export in Formate ohne Rechte: Warnung, Verschlüsselung, signierte ACLs.md
    [ ] Person hinzufügen auch in PostFix
    [x] Ordner umbenennen: passende Regeln in ACLs.md mitziehen (sonst greifen sie ins Leere)
[x] Papierkorb pro Projekt (.MyOS/Trash/), siehe core/Dokumentation/Designdocument Trash.md
[ ] Tests: ein einziger `pytest`-Lauf für alles (Scope-Tests legen `QGuiApplication` an, PostFix braucht `QApplication` – in einem Prozess bricht Qt ab; dazu Altlasten in `core/archive`)
[ ] Distribution erstellen
[ ] Demo virtualisieren (Remote-Desktop-Setup) zum Code-Schutz
[ ] Vielsprachigkeit vorbereiten (i18n/L10n)
[ ] Mailprogramm und Pfad (Idee 2026-11-05): ein Vorteil des einheitlichen Pfads. Beim Versenden erzeugt
    das Mailprogramm aus dem Pfad den Zusatz im Dateinamen ("2025 Rechnung Excalibur Projekt 203456-2 Obere Leitstelle"),
    den die Leute heute von Hand schreiben, damit die Datei auch außerhalb ihres Ordners zuzuordnen bleibt. Umgekehrt
    liest es solche Zusätze bei eingehenden Dateien und legt sie gleich im richtigen Projekt ab. Auch ein Teil hilft schon:
    Steht nur `/04_Finanz/Eingangsrechnungen` dabei, ist der Ordner klar, aber nicht das Projekt; dann fragt es nach oder
    schlägt per KI aus dem Kontext eines vor. Kommt die Projektnummer mit, umso besser.
[ ] Obsidian-MyOS-Plugin
[ ] MyOS auf einer Cloud (Idee 2026-11-05): Basisfunktionen als Plugin im Webclient, ohne Scope, SunTree und PostFix.
    Reihenfolge: erst OpenCloud oder ownCloud Infinite Scale (dasselbe Erweiterungssystem, klar dokumentiert), dann
    Nextcloud (eigenes Plugin); nicht ownCloud Classic (Support endet laut Wiki im Januar 2027)
    [ ] Kurzer Versuch: Test-Instanz per Docker, Demo-Daten hinein; wie verhält sich `.MyOS` im Web und per Sync-Client?
        Dabei prüfen: Laufwerk "Perspektiven" im Sync-Ordner, `.TagsHere.json` und `.MyOS/Trash` (Konflikte?), Vorlagen
        in einem geteilten `Templates`-Ordner
    [ ] Kleinster Prototyp: eine Ordneransicht zeigt blasse Ordner, eine hineingezogene Datei gebärt den Ordner. Zeigt,
        ob die Andockstellen reichen (Zeilen in die normale Dateiliste einfügen scheint nicht vorgesehen, ungeprüft)
    [ ] Dateiformat als kurze Beschreibung mit Testfällen für Python und JavaScript, bevor die Logik doppelt entsteht
        (zugleich der plattform-unabhängige Kern der Roadmap)
    [ ] Danach: Perspektiven als eigener Eintrag in der linken Leiste. Das Laufwerk fällt im Browser weg.
    [ ] Zugriffsrechte nicht im ersten Schritt: eine Browser-Erweiterung kann `ACLs.md` nicht erzwingen; auf dem Server
        lösen oder auf die Freigaben der Cloud abbilden
    [ ] ACL-Adapter zu Nextcloud (2026-11-07; vorgezogen: der Server setzt die Rechte dann wirklich durch, auch im
        Sync-Client). Ziel: Team folders (App groupfolders) mit "Advanced Permissions"; `ACLs.md` bleibt die Quelle,
        abgeglichen wird nur in eine Richtung. Grundlage: `myacl rules --json` (gebaut). Testinstanz: Nextcloud 32 auf dem
        GMXtec (Container `myos-nc`, nur 127.0.0.1:8081, per `ssh -L`); Ziel später: eine Nextcloud 32.0.1 eines Bekannten
        (ohne Admin-Zugang: braucht dort einen Team folder und "Manage advanced permissions")
        Versuch 2026-11-07 ergab:
        - Passt: pro Gruppe gewinnt die nächste Regel, tiefer auch weniger; mehrere Gruppen einer Person addieren sich
          (Erlauben schlägt Verbieten); read, write, create, delete getrennt wie bei uns; `change` ≈ "manage advanced
          permissions"; `execute` fehlt, dafür `share`
        - Leserecht auf jeden Elternordner ist Pflicht: ohne Leserecht an der Wurzel sieht man den Team folder gar nicht
          (403), auch mit Rechten tief unten. Abbildung: Leserecht auf den Weg, die Geschwister ausdrücklich sperren
          (`-read`) – geprüft, Tom sieht dann nur `Familie/Kind`
        - Lücke dabei: ein später neu angelegter Geschwisterordner erbt das Leserecht des Elternordners und ist sofort
          sichtbar. Ein Abgleich ab und zu reicht also nicht; die Sperre muss beim Anlegen entstehen (kleine
          Nextcloud-App, die auf neue Dateien reagiert) oder die Sichtbarkeit wird bewusst hingenommen
        - Gruppennamen unterscheiden Groß-/Kleinschreibung, Nextcloud hat schon `admin`: Gruppen des Adapters bekommen
          ein Präfix, sonst wird die Rolle `Admin` womöglich Admin der ganzen Nextcloud
        - Personen in `# Users` sind freie Namen, die Cloud braucht Konten: Zuordnung Name → Konto nötig
        - Basisrechte eines Team folders kennen nur read, write (= Ändern + Anlegen), share, delete
        [x] `myacl sync --plan`: die Nextcloud-Regeln berechnen, pro Person (Gruppen anlegen bräuchte einen Admin),
            jede Regel legt alle Bits fest, Leserecht auf den Weg samt Sperren daneben, die Gruppe des Team folders an der
            Wurzel ohne Rechte (core/acl_nextcloud.py; Konten in `.MyOS/Nextcloud.md`). Nicht abbildbar und gemeldet:
            Muster wie `/Job/*.pdf`, Ordner, die es noch nicht gibt (Embryos), `change`
        [x] `myacl sync --dry-run`: die vorhandenen Regeln lesen und nur den Unterschied zeigen (core/nextcloud_dav.py;
            gegen die Testinstanz geprüft, der Plan folgt dem Baum der Cloud). Über WebDAV
            (`PROPFIND`/`PROPPATCH` von `nc:acl-list`, ersetzt alle Regeln eines Pfads); braucht nur "Manage advanced
            permissions", kein `occ`. Bits: read 1, update 2, create 4, delete 8, share 16, dazu eine Maske
        [x] `myacl sync`: den Unterschied anwenden (pro Pfad die ganze Liste, die tiefsten zuerst, danach Kontrolle),
            fragt vorher oder braucht `--yes`. Auf der Testinstanz geprüft 2026-11-07: per WebDAV setzt Nextcloud danach
            genau die ACLs.md durch (Tom nur `Familie/Kind`, Lisa in `Finanz` nur lesen, Karl nur `Job`)
        [x] Neue Einträge auf dem Weg sofort sperren (Lücke oben): Nextcloud-App `cloud/nextcloud/myos_acl` (PHP,
            2026-11-07). `sync` markiert Wegregeln (Maske 15: Teilen wird geerbt, an der Wurzel für alle gesperrt, daher
            verlangt `sync` die Gruppen des Team folders), jeder Wegordner bekommt eine eigene; die App gibt neuen,
            verschobenen und kopierten Einträgen darin sofort dieselben Rechte ohne Lesen. Integrationstest gegen die
            Testinstanz grün. Verworfen: Freigaben statt Weg (Ordner am falschen Ort; das Konto darf nicht teilen),
            häufiger Abgleich (Zeitfenster bleibt). Die App braucht einen Admin, der sie einmal installiert
        [ ] Neu geborene Ordner, denen ACLs.md Rechte gibt: bleiben gesperrt bis zum nächsten `sync` (sicher, aber
            unbequem); später die App selbst ACLs.md lesen lassen oder `sync` nach jeder Geburt
        [ ] Beim Bekannten: ein Team folder, eine Gruppe mit allen Beteiligten, für uns "Manage advanced permissions"
        [x] MyOS-Ordner in der Files-App (Prototyp, 2026-11-07): eine eigene Zeile über der Dateiliste mit allen
            MyOS-Ordnern der Ebene beisammen, geborene voll, Embryos blass; Klick auf einen Embryo gebiert ihn; die
            geborenen verschwinden unten aus der Liste (Filter ohne Schaltfläche), dort bleibt das Eigene. Die Embryos
            rechnet MyOS (`.MyOS/Embryos.json` am Projekt), der Browser zieht nur das Geborene ab - kein zweites
            Regelwerk in PHP. Offizielle Schnittstellen von `@nextcloud/files` 3.12 (Header, FileListFilter).
            Verworfen: blasse Zeilen mitten in der Liste (keine Schnittstelle, der Desktop-Client würde sie als echte
            Ordner synchronisieren), Embryos als leere echte Ordner
        [ ] Stufe 2: `sync` schreibt `Embryos.json` und lädt die Vorlagen hoch; Geburt mit Dateien und `.MyOS` der
            Vorlage; `.MyOS` für alle im Projekt lesbar (sonst sieht, wer nur durchquert, keine Zeile); Embryos nur, wo
            man anlegen darf; "n hidden" zählt die herausgefilterten mit; Bündel verkleinern
        [ ] Tags: Unsere Tags auf die "Collaborative Tags" (WebDAV `systemtags`) spiegeln
### Nice to have
[ ] Ordner-Organisation neu
---

## ✅ Recent Milestones

- Perspective-Daemon (Resolver, FUSE, Scope-Client) mit Idle-Selbstabschaltung.
- Scope: Pfadleiste H/V, Edge-Dock-Modus, Kontextmenü Löschen, einheitliches `navigationRequested`.
- Verschachtelte Embryos werden von der Wurzel her geboren; Projekt-Root erfordert `.MyOS/Project.md`.
- `Project.md`-Metadaten werden atomar geschrieben (behebt zerschossenes Frontmatter durch parallele Schreiber).
- Desk: Projekt-Icon (`ProjectIcon`) + Remix-Icon-Set.
- ClipboardTool: CopyQ speichert Text-Clips als Markdown.
- PostFix modularisiert (Main entlastet, Verantwortlichkeiten klarer getrennt).
- PostFix Fast-Start und zentrale Interaktionsverbesserungen umgesetzt.
- Tag-Handling gehärtet (inkl. Security-Tests).
- Linux Markdown-Thumbnailer gebaut und integriert.
- Scope Tagbar mit Filterlogik (project/visible, OR-default) implementiert.
- Multi-Selection + Drag&Drop im Scope umgesetzt.
- Sicherheitsdialog für Ordner-Moves ergänzt.
- Batch-Move-API mit strukturierter Rückmeldung (`moved/skipped/errors`) ergänzt.
- Move-Report UX verbessert (lesbare Fehlgründe in Englisch).
- Tag-Design dokumentiert: Ordner-Tagging via Sidecar vorbereitet, aber MVP-seitig bewusst zurückgestellt.

---

## 💡 IDEAS (Backlog / später)

- Obsidian-Integration weiter ausbauen (optional bidirektionale Brücken).
- Projektübergreifende virtuelle Sichten (z. B. `/finanz` als Query View).
- Folder-Tagging-Semantik erweitern (nur bei echtem Bedarf).
- Undo/Recovery-Strategien für Move-Operationen.
- Room/Desk-Automation über Perspektiven-Kontext.

---

## 📐 DESIGN DOCS

- `Designdokument.md`
- `PostFix/Designdokument.md`
- `docs/INDEX.md` — zentrale Doku-Übersicht
- `core/Dokumentation/Designdocument Projects.md`
- `core/Dokumentation/Designdocument BlueprintLayer.md`
- `core/Dokumentation/Designdocument ACLs.md`
- `core/Dokumentation/Designdocument Tags.md`

---

## 📚 LEARNINGS & NOTES

- Kleine, atomare Commits + häufige Checks reduzieren Crash-Risiko bei großen UI-Refactors.
- Predictable behavior beats clever behavior (MVP-Regel).
- Dateibasierte, menschenlesbare Metadaten bleiben zentral für Souveränität und Debugbarkeit.
- Scope-DnD braucht Sicherheitsgeländer (insb. bei Ordnern), sonst entstehen stille Fehlverschiebungen.
- Obsidian-Kompatibilität ist wichtig, aber nicht auf Kosten klarer MyOS-Semantik.
- MVP-Fokus: reale Nutzung beobachten, dann gezielt erweitern (nicht alles vorab ausbauen).

---

## ❓ OFFENE FRAGEN

- ACL-UX: Wie einfach bleibt es für Nicht-Admins, ohne Sicherheit zu verwässern?
- Perspektiven: Persistenzmodell und Sharing-Strategie zwischen Projekten?
- Rooms: Wie eng koppeln wir an Desktop-Umgebung vs. MyOS-eigene Abstraktion?
- i18n: String-Management früh zentralisieren (Keys), aber ohne Over-Engineering.
- Demo-Virtualisierung: bestes Setup für Schutz + gute Demo-Performance?

---

## 📌 Nächste konkrete Slices

- Scope-Legacy-/Doppel-Kandidaten abarbeiten (`Scope/.Legacy-Code-Kandidaten.md`, `Scope/.FolderBrowser-DoppelKandidaten.md`).
- Entscheiden: `.TagsHere.json` versionieren oder ignorieren.
- ACL-MVP Scope festlegen (Datenmodell + 1 sichtbarer Flow).
- Perspektiven-MVP als minimalen nutzbaren Loop implementieren.
- Scope/PostFix UI-Polish-Liste priorisieren (Top 5 irritierende Punkte).
- Distribution-Prototype als reproduzierbaren Build dokumentieren.
- Demo-VM/Remote-Desktop als standardisierten Showcase vorbereiten.

---

> **Notiz:** Dieses Logbuch ist der operative Kompass. Es soll den echten Projektzustand widerspiegeln: klar, knapp, entscheidungsorientiert.
