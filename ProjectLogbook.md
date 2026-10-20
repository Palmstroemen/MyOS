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

[ ] ACLs
[ ] Perspektiven (MVP mit Resolver/FUSE/Daemon läuft; Persistenz/Sharing offen)
[ ] Rooms-Konzept (projektabhängige Desktops)
[ ] RecentFiles
[ ] Learning MyOS weiter ausbauen
[ ] Demodaten als Playground
[ ] Scope UI verfeinern  
    [x] FilesPanel: Doppelklick auf einen Ordner wechselt noch nicht in diesen Ordner
[ ] PostFix UI verfeinern und Exporter bauen
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
