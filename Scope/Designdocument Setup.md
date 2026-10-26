# Scope - Setup on the Back

The settings of MyOS's programs - Scope, the Headline (the minimal view M, becoming a tool of
its own docked at the top of the screen) and SunTree - are made on the back of Scope.
Decided on 2026-10-26.

## 1. The Picture

- **⚙ Setup** (in M's tools, later wherever Scope's top bar items go) flips Scope over: the
  window turns about its vertical axis (about 0.9 s: slow enough to be seen), and its back shows the settings. ⚙ on
  the back flips it back. Nothing opens or closes - the settings are the back of the thing
  they set. Both ways it turns in the same sense - one swing, and the panel turns through -
  and "⚙ Done" stands top left on the back, where ⚙ is on the front.
- **Tabs** on the back: **General**, **Scope**, **Headline**, **SunTree**.
- A change takes effect at once where it can (light/dark), and is kept: Scope today forgets
  light/dark and the language when it closes.

## 2. The Tabs

| Tab | Holds | When |
|---|---|---|
| General | light / dark, language, how pale embryos are - for the user "suggested MyOS folders" (live preview: a present folder beside a suggestion in each style, text, small and large icon, drawn as Scope's rows draw them; Scope follows at once, SunTree when it appears, 2026-10-26), and their badges, with a slider of their own (70 % by default); later the colour scheme (choose, edit) | step 1; scheme: steps 2, 3 |
| Scope | everything the rows' display menus held (the menus are gone, 2026-10-26): left one picture of a row as it really looks (the path bar's segments pushed together like tabs, its folders with a suggestion and a hidden one, the preview below), right check items and choices it follows - the two rows on/off (the projects row off by default; M keeps its CWD button), for both rows alike the path bar, suggested MyOS folders, hidden folders, the preview and its background, the folder style of each row, the preview's behaviour (reopen at once, timing soft / balanced / quick) | built |
| Headline | what concerns the docked tool: its tools, docking | with the Headline |
| SunTree | the crown's values (SunTree/Designdocument Krone.md, 5): line T, inner radius, Enter, Leave, fish-eye, softness, edge | step 1 |

Each value shows its default and can be set back to it.

**The small crown** (2026-10-26): left on the SunTree tab, a half crown with sample folders,
drawn with SunTree's own arithmetic (`Scope/CrownPreview.qml` on `SunTree/js/Crown.js`). Softly
glowing lines show the borders - inner radius (grey), line T (amber), where drawing in begins
(the field's edge, turquoise) and where it ends (the next level's start, magenta); each slider
has a dot in its line's colour. The exit at the edge is the rim running on past the first and
last folder, towards the stem (green).

One plays with it oneself (2026-10-26, a dive played at every change confused): the hand over
it moves the pointer as in SunTree - from the hollow out to the rim through a level and a half,
up and down through the folders - and the fan follows with the softness set; the hand shows
as a ring, the pointer SunTree would put as a dot. Moving a border
plays nothing, the line just moves. Over a slider its demo plays, in a loop: for the borders
the pointer goes where the value counts and the line pulses; over the magnifier the fan
breathes open and closed around the value set; over softness the hand (a ring) glides up and
down and the fan with its pointer follows - far behind and not to the ends when soft, close
to the hand when direct (jumps showed too little: the fan had caught up before the next); over the exit the pointer goes to the first folder
and the green rim pulses. Taking a slider stops it - the fan just follows the slider - and it
stays quiet until the mouse has left the row. A new value never starts anything by itself.
Half the stem is hinted on its left, the CWD oval's round end in the hollow, so one sees at
once what it is.

**Words for the user** (2026-10-26): crown, drawing in and line T mean nothing to the user. On
the tab SunTree is "the folder fan for quick dropping" and drawing in is "the change"; the
design documents keep their words. The sliders go from the inside out, as their lines lie in
the small fan, then the three that are no line; a line under each says what it does:

| Setting | Name | Says |
|---|---|---|
| inner | Size of the middle | the empty middle at the stem: every level starts there, back there the fan lets go |
| leave | Landing | how far among the subfolders one already is after the change |
| lineT | Way per level | how far the mouse moves outward until the folder fills the fan and one goes a level deeper |
| enter | Change begins | how deep in the folder the pointer is when the change into its subfolders begins |
| lens | Magnifier | how much the folder under the pointer is enlarged already at the start of a level |
| softness | Softness | how fast everything follows the hand (not in the small fan) |
| edge | Exit at the edge | how far one pushes past the first or last folder until the fan lets go (not in the small fan) |

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
   Begun (2026-10-26): light/dark and the language left the top bar (they are on General); the
   two rows (projects, MyOS folders) are switched on the Scope tab and kept in the settings
   file (`Scope/projectsRow`, `Scope/templatesRow`) - views of their own are to come; "Files
   50 %" (a transparency test) is gone with the files panel's half transparency; "Give project
   a theme" and "Enable sorting" (slipped in from development) are gone - a sort rule is now
   put in by hand (`.MyOS/Sort.md`). Then (2026-10-26): the filter moved to the Scope tab (a
   button showing the active filter opens its menu), narrow mode is gone, the edge-dock switch
   is gone (its code waits for the Headline). Left in the bar: ⚙, far left, and M. (⚙ cannot go
   into the window's title bar: the window manager draws it; a title bar of Scope's own would
   have to redo moving, resizing and snapping - perhaps with the Headline.)

## 5. Open

- Does SunTree take its colours from the scheme too (it has its own today)?
- Later on the Headline: signing in / switching user, switching off.
