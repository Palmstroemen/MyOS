# Scope - Setup on the Back

The settings of MyOS's programs - Scope, the Headline (the minimal view M, becoming a tool of
its own docked at the top of the screen) and SunTree - are made on the back of Scope.
Decided on 2026-10-26.

## 1. The Picture

- **⚙ Setup** (in M's tools, later wherever Scope's top bar items go) flips Scope over: the
  window turns about its vertical axis (about 0.9 s: slow enough to be seen), and its back shows the settings. ⚙ on
  the back flips it back. Nothing opens or closes - the settings are the back of the thing
  they set.
- **Tabs** on the back: **General**, **Scope**, **Headline**, **SunTree**.
- A change takes effect at once where it can (light/dark), and is kept: Scope today forgets
  light/dark and the language when it closes.

## 2. The Tabs

| Tab | Holds | When |
|---|---|---|
| General | light / dark, language; later the colour scheme (choose, edit) | step 1; scheme: steps 2, 3 |
| Scope | what Scope's top bar and display menu hold now: folder style, embryos, hidden folders, the files' share, preview | when the top bar goes |
| Headline | what concerns the docked tool: its tools, docking | with the Headline |
| SunTree | the crown's values (SunTree/Designdocument Krone.md, 5): line T, inner radius, Enter, Leave, fish-eye, softness, edge | step 1 |

Each value shows its default and can be set back to it.

## 3. One Settings File for All

- `~/.config/MyOS/MyOS.conf` (QSettings "MyOS"/"MyOS"), groups `General`, `Scope`, `Headline`,
  `SunTree`. Scope writes it; SunTree reads it each time it appears, so a change on the back
  of Scope shows the next time SunTree is called (it runs as a program of its own).
- `core/settings.py` holds the settings with their defaults and ranges in one place; both
  programs read through it. Values out of range or of the wrong kind fall back to the
  default (the file can be edited by hand).
- Scope's own `Scope.conf` (list columns, sorting) stays as it is.

## 4. Steps

1. `core/settings.py`, the flip with the tabs **General** (light/dark, language) and
   **SunTree** (its values); SunTree reads them on appearing; Scope keeps light/dark and the
   language. **Built** (2026-10-26): `Scope/SetupPage.qml` is the back
   (the Scope and Headline tabs say what will come there); ⚙ in M's tools and, until the top
   bar goes, in the top bar flips it (a `Rotation` of the window's content about the vertical
   axis, the back taking over at the quarter turn); Scope's backend offers `setting`,
   `setSetting`, `settingDefault`, `settingLimits`, `resetSetting`; SunTree reads its group
   in `turnedTo` (`crownSettings`).
2. Colour schemes to choose: the 34 colours move out of Scope's `main.qml` into scheme files
   (Dark, Light).
3. Colour schemes to edit: change colours, keep them as a scheme of one's own.
4. The **Scope** and **Headline** tabs, as the top bar is taken away.

## 5. Open

- Does SunTree take its colours from the scheme too (it has its own today)?
- Later on the Headline: signing in / switching user, switching off.
