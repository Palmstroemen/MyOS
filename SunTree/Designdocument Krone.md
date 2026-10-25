# SunTree - The Crown

SunTree is for dropping things into folders: it shows folders, no files, and has no search
(decided 2026-10-25). Today it is static: the folders of the CWD lie in two half rings, the
MyOS folders on the left, the other folders on the right, and the stem in the middle (the
CWD and its parents). The crown makes it move softly: one reaches deep folders by moving the
mouse outward, without clicking through levels.

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

## 4. Values

Tuned in the sketch, to be tuned further on the real desktop:

| Value | Default | Meaning |
|-------|---------|---------|
| Line T | 0.7 R | where the field fills the half and drawing in begins (0.5 R was the first idea; 0.7 R felt better) |
| Inner radius ri | 0.2 R | the stem's hollow; each level starts there |
| Lens | 2.2 | strength of the fish-eye at the start of a level |
| Softness | 10 /s | spring rate of the shown values |
| Scrolling | 1.0 | folders per hand movement along the ring |

One level takes 2 (T - ri) of hand movement outward: half of it growing, half drawing in.

## 5. In SunTree (QML)

- `Crown.js` (`.pragma library`) holds the state of a half: `s` (the one coordinate), `u`
  (per level the continuous folder index) and `lock` (the folders drawn into the stem).
  `move(state, dr, dt, geo, childCount)` takes the hand's movement, split into outward and
  along the ring; `pointer(...)` says where the pointer is drawn and which folder it is on.
- The two Canvas halves draw the rings from it; the backend gives each level's folders.
- **Pulling the pointer** is `QCursor.setPos` through a small backend slot, after each move:
  SunTree keeps the hand's position itself and sets the pointer where the crown draws it.
  This works on X11 (Cinnamon); Wayland does not let programs move the pointer.
- Open: how pulling the pointer goes with a real drag and drop of files under X11 - the main
  use of SunTree. If moving the pointer during a drag does not work, dropping needs its own
  way (e.g. the crown follows the hand without pulling while dragging).

## 6. Open

- Tweaks on the real desktop: curves, the line, softness, label sizes.
- Many folders on one level (a hundred): the fish-eye keeps the one under the pointer
  readable; the others become hairlines. Enough, or a scroll position shown at the edge?
- The top band (filters, clipboard) and the lens' frame in the moving crown.
