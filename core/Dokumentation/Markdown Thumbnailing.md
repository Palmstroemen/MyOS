# MyOS Markdown Thumbnailing (Linux)

## Goal

Show attractive previews for `*.md` files in common Linux file browsers (Nautilus, Dolphin, Nemo, Thunar where supported) using the Freedesktop thumbnail standard, without changing Markdown file content.

## Architecture

- **Renderer:** `core/thumbnailer/markdown_thumbnailer.py`
- **CLI entrypoint:** `core/bin/myos-md-thumbnailer`
- **Thumbnailer registration:** `installer/thumbnailers/myos-markdown.thumbnailer`
- **Installer integration:** `install.sh`

## Freedesktop Integration

`myos-markdown.thumbnailer` declares:
- MIME types: `text/markdown`, `text/x-markdown`
- command contract: `%i` input path, `%o` output png, `%s` requested size

Installed user-local to:
- `~/.local/share/thumbnailers/myos-markdown.thumbnailer`

CLI is linked to:
- `/usr/local/bin/myos-md-thumbnailer`

## Rendering Rules (Post-it Style)

- square PNG output (`size x size`)
- background color from markdown:
  - first `background_color: #hex` in YAML frontmatter
  - fallback: first body line matching same key
  - default: `#fff8b0`
- subtle border and top stripe for "note" look
- readable snippet (first meaningful lines, markdown syntax stripped)

## Security Rules

- remove script tags (`<script>...</script>`)
- strip HTML tags from preview text
- strip control characters
- markdown links render as text label only (`[label](url)` -> `label`)
- ignore executable URL schemes in preview context (`javascript:`, `data:text/html`)
- no execution of markdown/HTML/javascript during thumbnailing

## Performance Rules

- no network access
- no external process execution
- bounded output size (`64..1024`)
- small in-memory operations only

## Rollout (Suggested)

1. Enable current Linux thumbnailer flow (done in this phase).
2. Add optional cache invalidation helper for development/debugging.
3. Expand metadata support (e.g., project tint fallback from `.MyOS` context).
4. Add non-Linux adapters later (Windows preview handlers, macOS QuickLook plugin).
