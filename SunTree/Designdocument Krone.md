# SunTree - The Crown

SunTree is for dropping things into folders: it shows folders, no files, and has no search
(decided 2026-10-25). Today it is static: the folders of the CWD lie in two half rings, the
MyOS folders on the left, the other folders on the right, and the stem in the middle (the
CWD and its parents). The crown makes it move softly: one reaches deep folders by moving the
mouse outward, without clicking through levels.

**One action, then gone** (2026-10-26). SunTree is a grip, not a window: a shortcut calls it,
one does one thing, and it disappears. Every action is also the way out, so one is not caught
in it. Uses, all of this shape:

1. **Dropping files** - drag files (from Nemo, a browser, Scope), call SunTree, find the
   folder, drop; on an embryo it is born by it. Perhaps copying instead of moving with a key
   held at the drop.
2. **Changing the CWD** - double-click a folder; Scope follows, as the place is shared.
3. **Putting a lens on or taking it off** - a filter or a perspective.
4. **Collecting into the Clipboard** - files from several places dropped one after another
   onto the Clipboard at the top of the stem, each a short call of its own.
5. **Dropping from the Clipboard** - an entry dragged from the Clipboard into a folder of the
   crown, all inside SunTree.
6. **Opening a folder** - Scope opens exactly there (middle click or a key): a quick jump to a
   place, not only a change of the CWD.
7. **Only looking** - where am I, which lens is on? The one use without an action, so
   cancelling must always work: Esc, the shortcut again, a click beside the crown.

What follows from it:

- After the action SunTree is gone, so one no longer sees where the files went: a short
  notice ("3 files -> Belege/03"), perhaps with undo, so a wrong drop is not annoying.
- SunTree appears with the stem under the pointer: the hand starts in the hollow and every
  direction is a way into the crown, like a pie menu.
- The way back out of the stem matters mostly for dropping (one level too deep, out again);
  it does not close SunTree.
- **The shortcut during a drag** works (tried on 2026-10-26 in Xephyr with a GTK 3 drag
  source, as Nemo): both a passive key grab on the root window (how desktop shortcuts are
  bound) and an XRecord listener (how pynput's `GlobalHotKeys` listens) get Ctrl+Alt+Space
  while the drag is held, and the drag goes on; so does SunTree's own service. Not yet tried
  under Cinnamon itself.

Decided on 2026-10-25 with a clickable sketch: `SunTree/prototype/Krone.html` (open it in a
browser; the artifact "SunTree Krone" is the same page). The arithmetic is
`SunTree/js/Crown.js`, tested in `SunTree/tests/test_crown.py`.

## 1. The Picture

The tree draws its branches inward and makes them part of its stem.

1. **Growing.** The further the mouse goes outward in a folder's field, the wider that field
   gets and the narrower the others (a fish-eye). At the same time the inner ring pulls back
   towards the centre, and outside it a second ring shows the field's subfolders, each
   folder's subfolders in its own slice.
2. **At the line T** the inner ring's outer edge has pulled back to T, and the field fills the
   whole half (180°).
3. **Drawn in.** Beyond T the hand moves on outward, but the pointer is pulled inward: the
   field shrinks into the stem's hollow, its subfolders take the whole ring, and the folder
   appears in the stem. When the field is gone, the next level starts as the first did, with
   the pointer at the inner radius.
4. **Back.** Moving inward runs everything backwards: the pointer is pushed outward, the
   folder comes out of the stem and becomes a field again.
5. **Up and down** within a ring scrolls through all folders of the level: the neighbouring
   field grows again. With the field filling the half, the pointer moves evenly with the hand
   and the neighbouring field grows past it (following the field strictly, the pointer would
   fly across the half at every change).
6. **Folders without subfolders** grow to the whole half but are not drawn in.
7. **Letting go.** The pointer is free again back in the stem's hollow, over the top or bottom
   edge while the first field is still small, or with Esc; the crown then runs back softly
   through all levels.

## 2. What It Does

- Diving is only showing. A drop puts the file into the folder under the pointer (an embryo
  is born by it); a click goes into it (the CWD, and Scope follows, as the place is shared).
  The folders drawn into the stem are shown there as a preview (dashed).
- Both halves: on the left the MyOS folders (born or embryo, embryos pale), on the right the
  other folders. The lens works as before (Designdocument Perspective Resolver MVP.md, A3).

## 3. Soft Everywhere

- All shown values follow their targets with a spring, so nothing jumps.
- The stem: folders glide from place to place. Going into a folder, it glides from the crown
  into the stem and pushes the CWD and its parents down.
- **The way back** (2026-10-25): a click on a folder lower in the stem (a parent) does not
  jump either. The folders between it and the CWD are pushed up the stem and spat out into
  the crown, the reverse of drawing in: the clicked parent becomes the CWD, the folder one
  came from opens as a field of it, and the crown settles at its first level.

## 4. The Stem From Top to Bottom

- **The Clipboard** sits at the top of the stem (2026-10-25), not in the top band: the
  multiclipboard, where every copy lands and which travels into all projects. One drops onto
  it like onto any folder.
- **The lens' frame** (✕ and the lens' levels) below it, while a lens is on: it pushes the
  Clipboard up.
- **The CWD** in the middle (the oval), with the folders drawn into the stem above it as a
  preview while diving.
- **The parents** below it, down to the root.

## 5. Values

Tuned in the sketch, to be tuned further on the real desktop:

| Value | Default | Meaning |
|-------|---------|---------|
| Line T | 0.7 R | where the field fills the half and drawing in begins (0.5 R was the first idea; 0.7 R felt better) |
| Inner radius ri | 0.2 R | the stem's hollow; each level starts there |
| Lens | 2.2 | strength of the fish-eye at the start of a level |
| Softness | 10 /s | spring rate of the shown values |
| Scrolling | 1.0 | folders per hand movement along the ring |

One level takes 2 (T - ri) of hand movement outward: half of it growing, half drawing in.

## 6. In SunTree (QML)

- `Crown.js` (`.pragma library`) holds the state of a half: `s` (the one coordinate), `u`
  (per level the continuous folder index) and `lock` (the folders drawn into the stem).
  `move(state, dr, dt, geo, childCount)` takes the hand's movement, split into outward and
  along the ring; `pointer(...)` says where the pointer is drawn and which folder it is on.
- The two Canvas halves draw the rings from it; the backend gives each level's folders.
- **Pulling the pointer** is `QCursor.setPos` through a small backend slot, after each move:
  SunTree keeps the hand's position itself and sets the pointer where the crown draws it.
  This works on X11 (Cinnamon); Wayland does not let programs move the pointer.
- Pulling the pointer during a drag works (tried on 2026-10-25 in a nested X server,
  Xephyr, with a Qt and a GTK 3 drag source - GTK as Nemo): after `QCursor.setPos` the drag
  goes on from the new place with the hand's next movement, and the file is dropped there.
  The drop target learns the new place only with that next movement.

## 7. Open

- Tweaks on the real desktop: curves, the line, softness, label sizes.
- **Caught in the tree** (first try on the real desktop, 2026-10-25): while a half holds the
  pointer it is put back where the crown draws it, so one can hardly leave the window; it
  lets go only back in the hollow, over the top or bottom edge while the first field is
  small, or with Esc. Ways out, perhaps combined: over the top or bottom edge on every
  level; a strong, fast move (pulling away on purpose); across the stem into the other half.
  Mostly solved by "one action, then gone" (2026-10-26): the drop, the click and the lens are
  the ways out. What remains is cancelling (Esc, the shortcut again, a click beside the crown).
- SunTree closing itself after an action, the notice with undo, appearing under the pointer.
- The global shortcut needs `pynput` (installed on 2026-10-26); without it SunTree reports
  "missing-pynput" and stays a normal window. Its default was "<ctrl>+<alt>+space", which
  pynput rejects ("<space>" is right), so the service failed silently: fixed, and SunTree's
  own service tried during a drag in Xephyr.
- The way back out of the stem (spitting folders out) is not built yet; a parent clicked
  in the stem is gone into at once.
- Drawing in, the preview and the CWD oval overlap restlessly in the middle of the glide.
- Many folders on one level (a hundred): the fish-eye keeps the one under the pointer
  readable; the others become hairlines. Enough, or a scroll position shown at the edge?
- The top band (filters) in the moving crown.
