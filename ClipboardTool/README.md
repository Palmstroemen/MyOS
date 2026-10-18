# CopyQ MyOS Clipboard Integration

Saves text clipboard contents as Markdown files in your MyOS Clipboard folder. File/folder copies are ignored. Works with QuoteURLText or Excerpt with Link for web clipping with source URLs.

## Requirements

- **CopyQ** (v4 or later)
- **Python 3**
- No MyOS core dependency; only path convention and environment variables

## Setup

### 1. Set environment variables

- **`MYOS_CLIPBOARD_PATH`** – Target directory for clip files (e.g. your project’s `Clipboard` folder).
  - Example: `~/Dokumente/MyOS/MyOS_Test/Clipboard`
  - Fallback if unset: `~/Clipboard`

- **`MYOS_CLIPBOARD_TOOL_SCRIPT`** (optional) – Full path to `save_clip_to_myos.py` if it is not at:
  - `~/Dokumente/MyOS/ClipboardTool/save_clip_to_myos.py`

To set for your session:

```bash
export MYOS_CLIPBOARD_PATH="$HOME/Dokumente/MyOS/MyOS_Test/Clipboard"
# optional, if ClipboardTool is elsewhere:
export MYOS_CLIPBOARD_TOOL_SCRIPT="$HOME/Dokumente/MyOS/ClipboardTool/save_clip_to_myos.py"
```

Make sure CopyQ is started with these variables (e.g. from the same shell, or via your desktop autostart).

### 2. Load commands in CopyQ

1. Open CopyQ.
2. **File → Load Commands…** (or **Commands/Global Shortcuts…** and then Load).
3. Select `copyq-myos-save-auto.ini` and `copyq-myos-save-manual.ini` from this folder (or load both in one go).
4. Confirm with **OK** / **Apply**.

### 3. (Optional) Web clipping with source URL

For “copy selection + URL” from the browser:

- **QuoteURLText** – Template for title, URL, date (e.g. Markdown).  
  [Support](https://qoelabs.com/)
- **Excerpt with Link** – Copies selection and page URL in one action (Chrome).

Clip text with one of these; the auto-save command will store it (including any URL in the text) as a Markdown file in `MYOS_CLIPBOARD_PATH`.

## Commands

| Command | Trigger | Effect |
|--------|---------|--------|
| **MyOS \| Auto-Save Clipboard to MD** | Automatic on clipboard change | If the clipboard has plain text and no file list (`text/uri-list`), writes `clip_YYYYMMDD_HHMMSS.md` in `MYOS_CLIPBOARD_PATH`. |
| **MyOS \| Save to Clipboard (MD file)** | From CopyQ menu (right‑click or Item menu) | Saves the selected item(s) as one MD file per item. |

## File format

Each saved file:

- **Filename:** `clip_YYYYMMDD_HHMMSS.md`
- **Content:** Optional YAML frontmatter (`source:` URL if detected, `copied:` timestamp) and the clipboard text.

Example:

```markdown
---
source: "https://example.com/page"
copied: "2026-02-27 14:32"
---

The copied text here...
```

## Troubleshooting

- **Nothing is saved**  
  - Check `MYOS_CLIPBOARD_PATH` and that CopyQ was started with it set.  
  - Ensure the path exists or is writable (the script creates the directory if missing).  
  - For auto-save: copying files (e.g. in a file manager) is ignored on purpose; only plain-text copies are saved.

- **Wrong script path**  
  - Set `MYOS_CLIPBOARD_TOOL_SCRIPT` to the full path of `save_clip_to_myos.py`, or place ClipboardTool at `~/Dokumente/MyOS/ClipboardTool/`.

- **CopyQ doesn’t see env vars**  
  - Start CopyQ from a terminal where you `export` the variables, or set them in your desktop/autostart configuration so they apply when CopyQ starts.
