# MyOS Markdown Thumbnailer

This component adds markdown thumbnails for Linux file browsers that implement
the Freedesktop thumbnailer standard (for example Nautilus, Nemo, Caja).

## Visual behavior

- Short notes are rendered as sticky notes (Post-it style).
- Longer notes are rendered as notebook pages (Notizblock/Heft style).
- If markdown frontmatter contains `background_color: "#rrggbb"`, that color is used.
- Optional frontmatter `note_style` (or `myos_note_style`) can override style manually.

## Manual note styles

Supported style values (aliases in German/English are accepted):

- `postit` - short sticky note
- `sheet` / `a4` / `mitschrift` - A4 page style
- `notebook` / `heft` / `konzept` - notebook concept page
- `cloud` / `gedankenskizze` - thought cloud card
- `chat` / `ai-chat` / `sprechblase` - speech bubble style
- `config` / `konfiguration` - config/settings card

## Files

- `scripts/myos_md_thumbnailer.py` - renderer script
- `installer/myos-md.thumbnailer` - thumbnailer template
- `installer/install-thumbnailer.sh` - local installer helper

## Install (per user)

From project root:

```bash
chmod +x installer/install-thumbnailer.sh scripts/myos_md_thumbnailer.py
./installer/install-thumbnailer.sh
rm -rf ~/.cache/thumbnails/*
```

Then restart/reopen your file browser.

## Frontmatter example

```markdown
---
background_color: "#ffe082"
note_style: "mitschrift"
---
# Einkauf
Milch
Zimt
Nudeln
```

## Notes

- Renderer tries Pillow first, then falls back to PySide6.
- If both are missing, thumbnail generation fails silently for the browser.
- Thumbnailers are asynchronous: previews may appear with a short delay.
