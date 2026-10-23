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
    [ ] Regel bequem einrichten (heute: Knopf "Enable sorting" im aktuellen Ordner oder von Hand); myls zeigt virtuelle Ebenen noch nicht
[ ] SunTree
[ ] Perspektiven (Brille): Verhalten festgelegt (Designdocument Perspective Resolver MVP.md, Teil A, 2026-10-22);
    Umsetzung: eine Sitzung im Daemon, FUSE zeigt den ganzen umgedrehten Baum, QML/SunTree ohne eigenen Pfadbau
    [x] E1 Sitzung im Kern  [x] E2 Laufwerk "Perspektiven" + Daemon  [ ] E3 Scope  [ ] E4 rechtes Menü  [ ] E5 SunTree  [ ] E6 Filter
[ ] ACLs
[ ] Perspektiven (MVP mit Resolver/FUSE/Daemon läuft; Persistenz/Sharing offen)
[ ] Rooms-Konzept (projektabhängige Desktops)
    [x] Desktop folgt den Projekten: Theme, Taskleisten-Theme (PanelTheme), Hintergrund; Änderungen werden automatisch gespeichert
    [ ] Beim Umschalten des Taskleisten-Themes ordnet Cinnamon die Fenster in der Taskleiste neu an (beobachten)
    [x] Taskleisten-Programme pro Projekt (`## Taskbar`; Cinnamon, GNOME)
    [ ] Taskleiste unter KDE; Programmnamen statt .desktop-Kennungen in Scope
[ ] RecentFiles
[ ] Learning MyOS weiter ausbauen
[ ] Demodaten als Playground
[ ] Scope UI verfeinern  
    [x] Röntgenblick (X-Ray): kleine Ordner durchsichtig, solange die Liste ohne Scrollbalken passt; Standard an; auch `myls --roentgen`
    [ ] Röntgenblick: besseres Icon für den Button
    [x] FilesPanel: Doppelklick auf einen Ordner wechselt noch nicht in diesen Ordner
    [x] P-Button: macht den angewählten Ordner, sonst (ohne Auswahl) den angezeigten zum Projekt; durchgestrichenes P macht ein Projekt wieder zum Ordner; P-Badge auf Projektordnern
    [x] Umbenennen in der Ordnerleiste: Feld zeigt den alten Namen (war leer); F2 benennt die Auswahl im FilesPanel um
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
