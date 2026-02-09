---
# Ordner-Tags (gelten für alle Dateien im Ordner)
folder-tags: [projekt-abc, q1-2024, aktiv]

# Datei-spezifische Tags (Overrides)
file-tags:
  konzept.md: [draft, brainstorm]
  präsentation.md: [wichtig, client-facing]
  
# Export-Voreinstellungen
export-defaults:
  pdf:
    template: firmen-template.tex
    paper: a4
  pptx:
    template: corporate.pptx
    theme: dark
---

# Ordner-Notizen

Dieser Ordner enthält die Unterlagen für Projekt ABC.

## Workflow
1. Konzept in `konzept.md` schreiben
2. Mit `python folder_tags.py export --file konzept.md --format pptx` exportieren
3. Präsentation finalisieren

## Tags-Erklärung
- `#aktiv`: Noch in Bearbeitung
- `#client-facing`: Für Kunden bestimmt
- `#draft`: Erster Entwurf