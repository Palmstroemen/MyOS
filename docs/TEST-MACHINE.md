# Test Machine

Several people play through the tutorial one after the other on one computer
(`scripts/testrun.py`, decided 2026-10-26). Each tester gets a fresh copy of the tutorial,
writes comments into one note, and at the end clicks **"✅ Bin fertig – Rechner für den
nächsten Tester vorbereiten"** in lesson 16. Their work is collected, everything is reset,
and lesson 1 opens for the next tester.

## Setting it up (once)

1. Linux with an X11 session (Cinnamon, GNOME on Xorg, ...), one user account for all testers.
2. The repository, e.g. `~/MyOS`, and its dependencies:
   ```
   sudo apt install python3-pip ffmpeg wmctrl
   pip install -r requirements-full.txt
   ```
3. Open the tutorial at every login, and SunTree (lesson 15) ready for Ctrl+Alt+Space:
   ```
   python3 scripts/testrun.py install
   python3 SunTree/install_autostart.py ~/MyOS-Tutorial/DE
   ```
4. Make the first copy and open lesson 1: `python3 scripts/testrun.py start`.
5. Check: lesson 1 shows in PostFix; in lesson 7, "▶ Übung öffnen" opens Scope and the file
   browser side by side; "💬 Kommentar zu dieser Lektion" opens "Meine Kommentare".

## What a tester sees

- PostFix with lesson 1 of the copy (`~/MyOS-Tutorial`, German). The repository is never
  touched.
- Under every lesson "💬 Kommentar zu dieser Lektion": it opens the note "Meine Kommentare"
  as a sticky note and adds a heading for the lesson.
- Exercise links ("▶ Übung öffnen") open Scope in the exercise folder.
- At the end of lesson 16 "✅ Bin fertig": asks first, with an optional name.

## What "Bin fertig" does

1. Closes the Scope and PostFix windows showing the copy (other windows stay).
2. Collects into `~/MyOS-Testergebnisse/<date>_<time>_<name or Tester_N>/`:
   - `Meine Kommentare.md` - the comments,
   - `Änderungen.md` - every note added, changed (with a diff) or gone (moved or deleted),
   - `Neu/`, `Geändert/` - those files themselves,
   - `Einstellungen/` - the tester's MyOS and PostFix settings,
   - `Zusammenfassung.md` - name, start, end, counts.
   PostFix's window place in a note's front matter (`window_...`) is no change.
3. Deletes the copy and makes a fresh one; resets `~/.config/MyOS` and `~/.config/PostFixDev`.
4. Opens lesson 1.

By hand: `python3 scripts/testrun.py finish --name "Anna"` (add `--no-restart` to only
collect and reset), `python3 scripts/testrun.py prepare` (reset without collecting).
`MYOS_TUTORIAL_DIR` and `MYOS_RESULTS_DIR` move the copy and the results.

## Safety

- `prepare` only deletes a folder it made itself (marker file `.myos-tutorial-copy`).
- The copy is built from the lessons as last committed (`git archive HEAD`), not from the
  working files: a lesson opened in the repository itself (PostFix saves window places into
  notes) never reaches a tester. Without git the working files are copied.
- "Bin fertig" and "Kommentar" only work in notes inside such a copy, and "Bin fertig" asks.
- Exercise links only open folders inside their own lesson.

## Known limits

- The classic file browser opened by lesson 7 stays open after "Bin fertig" (on the old,
  deleted folder); testers close it themselves.
- The links work in PostFix only (not in Obsidian); English lessons have no comment links.
- Following "zur nächsten Lektion" shows the next lesson in the same PostFix window, but
  editing still applies to the note opened first - comments therefore go into their own note.

