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
            [x] Schritt 1: Knopf M, eine Zeile, Dropdown bis "Projekte", Kaskade nach rechts; schmale Knöpfe, 1x Suche und Clipboard
            [x] Clipboard (Multiclipboard, wandert in alle Projekte mit) als kleiner Icon-Knopf: in den Werkzeugen von M
            [x] Werkzeuge von M (2026-10-26): Knopfzeile oben im CWD-Dropdown statt Menü - Clipboard, Suche, Hell/Dunkel,
                Sprache, versteckte Ordner (Scope/CwdTools.qml); M wird ein eigenes, oben angedocktes Werkzeug (kein H, kein E)
            [x] M bleibt eine Zeile (2026-10-26): MyOS-Ordner brechen nicht mehr in eine zweite Zeile um; Mausrad schiebt
            [ ] Setup auf der Rückseite von Scope (Scope/Designdocument Setup.md): ⚙ dreht Scope um; Tabs Allgemein, Scope,
                Headline, SunTree; eine Einstellungsdatei für alle (core/settings.py, ~/.config/MyOS/MyOS.conf)
                [x] Schritt 1 (2026-10-26): Umdrehen, Hell/Dunkel und Sprache (bleiben jetzt gespeichert), SunTree-Werte
                [x] Kleine Krone im SunTree-Tab (2026-10-26): leuchtende Grenzlinien, Tauchgang bei jeder Änderung
                [ ] Schritt 2: Farbschemata wählen  [ ] Schritt 3: bearbeiten  [ ] Schritt 4: Tabs Scope und Headline
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
        [ ] E7 Suche mit Brille über alle Projekte (nur die Abteilungsordner, Spalte "Projekt"; Designdoc A9) -
            zurückgestellt (2026-10-25), bis die Suche im Alltag fehlt; schlank wäre: nur Dateinamen, ein Feld in Scope
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
    [x] FilesPanel: Doppelklick auf einen Ordner wechselt noch nicht in diesen Ordner
    [x] P-Button: macht den angewählten Ordner, sonst (ohne Auswahl) den angezeigten zum Projekt; durchgestrichenes P macht ein Projekt wieder zum Ordner; P-Badge auf Projektordnern
    [x] Umbenennen in der Ordnerleiste: Feld zeigt den alten Namen (war leer); F2 benennt die Auswahl im FilesPanel um
    [ ] FilesPanel Rasteransicht immer nach Name aufsteigend (oben MyOS-Ordner und Embryos, darunter Unterprojekte
        und andere Ordner); heute übernimmt sie die Spaltensortierung der Listenansicht, ohne sie anzuzeigen
    [ ] FilesPanel: Embryos erscheinen nicht halbtransparent (sollten sie, wie in den Ordnerleisten)
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
[ ] Obsidian-MyOS-Plugin
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
