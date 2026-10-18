# Scope — MyOS File Browser

QML-based file browser for MyOS: project and template navigation, tags, and file operations.

## Overview

- **Two browser rows:** Templates (standard folders / embryos) and Projects (CWP and subprojects). Each row can show a path breadcrumb and folder list; Templates can run in perspective or plain CTD mode.
- **Concepts:** CWD/CWP (current working directory/project) and CTD (current target directory) for preview and file list. See [Vision/GUI Filebrowser.md](../Vision/GUI%20Filebrowser.md) for definitions and [main.qml](main.qml) comment block for code mapping.
- **Files area:** File list with tag filter, multi-selection, drag & drop, context menu. Optional side panel with folder/file tags; Leave button to step out of `.MyOS` when in config view.
- **Dialogs:** All dialogs are in `Scope/Dialogs/` (e.g. move, rename, create folder, filter save, config prompt). Main window only instantiates them.

## Run

Start the Python backend and QML UI:

```bash
python3 Scope/Scope.py
```

Requires Qt 5 (QtQuick 2.15, QtQuick.Controls 2.15) and the `core` API (Scope.py bridges to `core.scope_api`).

## Layout

- **main.qml:** Application window, theme, CWP/CTD state, `standardFolders` / `subProjects`, and the two `FolderBrowser` instances (Templates, Projects) plus `FilesPanel`. Path helpers live in `js/PathUtils.js` and `js/FolderBrowserUtils.js`.
- **FolderBrowser.qml:** Reusable folder bar (path segments, folder list, preview, drag/drop). Used for both template and project rows.
- **FolderItem.qml:** Single folder/item chip (text, smallIcon, largeIcon); opacity follows `fillColor.a` when half-transparent.
- **FilesPanel.qml:** File list, tag panel (adapts to tag width), P/Config/Leave buttons, tag chips.

## Backend

`Scope/Scope.py` loads the core API and exposes it to QML as `backend`. It provides e.g. `listChildren`, `listTemplates`, `listEntriesFiltered`, `moveEntry`, `createProject`, and project/config helpers.
