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
  notice ("3 files -> Belege/03") with undo, so a wrong drop is not annoying.
- **Built** (2026-10-26): a drop, a double click (a folder in the crown, a parent or the
  Clipboard in the stem: going in and away), putting a lens on (double click on the left)
  and taking it off (✕) put SunTree away; a single click only goes in, to look further.
  The notice is a window of its own at the bottom of the screen, six seconds, with Undo:
  each file goes back where it came from, also when a sorted folder filed it on, and a
  folder the drop emptied (an embryo again) is born again by it. A folder born by the drop
  becomes an embryo again when undo empties it.
- **No background** (2026-10-26): the window is transparent, only the crown and the stem are
  drawn over what lies below (it needs a compositor, as Cinnamon has). A click beside them,
  in the margin or the empty corners, puts SunTree away - the cancelling of use 7; a click in
  the hollow or on the stem between the halves does not.
- **The stem's panel** (2026-10-26): between the halves, behind the stem, what lies below
  shows blurred (about 10 px) and darkened (black, 35 %), with rounded corners. Muffin offers
  no blur behind windows, so SunTree takes a snapshot of that rectangle just before it shows
  (`takeBackdrop`, kept in memory only) and blurs it (`MultiEffect`). Where the screen cannot
  be read (Wayland) only the tint remains.
- SunTree appears with the stem under the pointer: the hand starts in the hollow and every
  direction is a way into the crown, like a pie menu.
- **Built** (2026-10-26): on the shortcut SunTree places its window so the CWD in the
  middle of the stem lies under the pointer, then takes the panel's snapshot and shows. At
  a screen edge the window stays whole and is pushed aside, and the pointer is pulled into
  the middle of the stem, as the crown pulls it anyway: not a jump but a ride the eye can
  follow (350 ms, easing in and out). SunTree shows only when the pointer is there - shown
  at once, its loading held the ride up and it hopped. Going away, the pointer rides back
  where SunTree picked it up; after the red X too, which ends SunTree once it is back.
- **Fading away** (2026-10-26): SunTree does not vanish at once. A snapshot of it
  (`ShaderEffectSource`, not live) blurs strongly (blurMax 64), fades out and draws together towards the stem (to
  60 %) over 300 ms, slowly at first; then the window hides and the crown is back at rest.
  Fading and drawing together are animators on the render thread, smooth even when the GUI
  thread is busy. Meanwhile the pointer rides back across the window: nothing there reacts,
  not even to hovering - a half took the pointer on its way and pulled it into the crown
  again, which made the first fade jerky. The red X ends SunTree when both are done.
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
7. **Letting go.** The pointer is free again back in the stem's hollow, with Esc, or pushed on
   past the first or last folder of any level, towards the stem (2026-10-26: before, one was
   caught there sideways). The push adds up over small moves; moving back from the end starts
   it again, so a nudge while scrolling does not let go. The crown then runs back softly
   through all levels, and the half takes the pointer again only after the hand has left it.

## 2. What It Does

- Diving is only showing. A drop puts the file into the folder under the pointer (an embryo
  is born by it); a click goes into it (the CWD, and Scope follows, as the place is shared).
  The folders drawn into the stem are shown there as a preview (dashed).
- Both halves: on the left the MyOS folders (born or embryo, embryos pale), on the right the
  other folders. The lens works as before (Designdocument Perspective Resolver MVP.md, A3).

- **Looking, not going: the CTD** (2026-10-26). The middle of SunTree shows the CTD, the
  folder SunTree shows; on appearing it is the CWD. A single click - in the crown or on the
  stem - only moves the CTD there (drawn in or spat out); the CWD, Scope and the desktop stay.
  A double click makes it the CWD and SunTree goes away. A drop lands as before. The lens
  changes only deliberately: a double click on the left (on, sharper) or its frame (flatter,
  ✕); a single click on the left only looks into a born folder.
- **The CWD glows** wherever it shows: as the oval while CTD and CWD are one, as a button
  lower in the stem when one looks deeper, as a field in the crown when one looks higher -
  light around it in its project's colour lit up (white without one), a bright frame, bold.
  Drawn as strokes widening and fading outward: the canvas' shadowBlur stalled the animations.
  Scope is to mark its CWD the same way (a later step).

## 3. Soft Everywhere

- All shown values follow their targets with a spring, so nothing jumps.
- The stem: folders glide from place to place. Going into a folder, it glides from the crown
  into the stem and pushes the CWD and its parents down.
- **The way back** (2026-10-25): a click on a folder lower in the stem (a parent) does not
  jump either. The folders between it and the CWD are pushed up the stem and spat out into
  the crown, the reverse of drawing in: the clicked parent becomes the CWD, the folder one
  came from opens as a field of it, and the crown settles at its first level.
- **Built** (2026-10-26): going up, the crown starts as if one had dived from the parent
  down to the old CWD and runs back to rest as when letting go; the stem shows the folders on
  the way as previews above the new CWD while they come out. The stem's entries glide: the
  parent from its place into the oval, the old CWD from the oval to its preview. The half is
  the one the way lies in (right, or left for MyOS folders); where the way is not in the crown
  (a lens on), SunTree goes up as before.

## 4. The Stem From Top to Bottom

- **The Clipboard** sits at the top of the stem (2026-10-25): the multiclipboard, where every
  copy lands and which travels into all projects. One drops onto it like onto any folder.
  Beside it the red X, an emergency exit that quits SunTree, until we find it is not needed.
  The top band (filter buttons, "Dummy Ablage", development helpers) is gone (2026-10-26).
- **The lens' frame** (✕ and the lens' levels) below it, while a lens is on: it pushes the
  Clipboard up.
- **The CWD** in the middle (the oval), with the folders drawn into the stem above it as a
  preview while diving.
- **The parents** below it, down to the root.

- **Geometry** (2026-10-26): the halves' centres are the centres of the CWD oval's round
  ends (radius half its height), so the hollow lies around them; the stem is exactly as wide
  as the space between (154 px, the oval 226 x 72). The stem's buttons are square; only the
  CWD oval is round, its corners growing as an entry glides into it.

## 5. Values

Tuned in the sketch, to be tuned further on the real desktop:

| Value | Default | Meaning |
|-------|---------|---------|
| Line T | 0.7 R | where the field fills the half and drawing in begins (0.5 R was the first idea; 0.7 R felt better) |
| Inner radius ri | 0.2 R | the stem's hollow; each level starts there |
| Lens | 2.2 | strength of the fish-eye at the start of a level |
| Softness | 10 /s | spring rate of the shown values |
| Scrolling | 1.0 | folders per hand movement along the ring |
| Edge | 0.08 R | push past a level's first or last folder that lets go |

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
  the ways out. Caught sideways at the first or last folder: solved, pushing on past it lets
  go on every level (1, point 7). What remains is cancelling (the shortcut again, a click
  beside the crown).
- SunTree's texts are not translated yet (no `.ts` for SunTree; the new ones use qsTr).
- The global shortcut needs `pynput` (installed on 2026-10-26); without it SunTree reports
  "missing-pynput" and stays a normal window. Its default was "<ctrl>+<alt>+space", which
  pynput rejects ("<space>" is right), so the service failed silently: fixed, and SunTree's
  own service tried during a drag in Xephyr.
- Drawing in, the preview and the CWD oval overlap restlessly in the middle of the glide.
- Many folders on one level (a hundred): the fish-eye keeps the one under the pointer
  readable; the others become hairlines. Enough, or a scroll position shown at the edge?
