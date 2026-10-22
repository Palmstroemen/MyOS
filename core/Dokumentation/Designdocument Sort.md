# MyOS Sort Profiles - Design Document

## 1. Purpose

Many people keep files in `/Year/Month/` structures (photos, invoices, ...). MyOS takes that
work off them: a folder can carry a sort rule, and MyOS files what lands in it by date - but
only as far as a structure actually helps. A project with two invoices keeps them flat in
`/Rechnungen`; everybody finds them there.

Sections 2-9: the concept decided on 2026-10-22, built the same day (section 10).

## 2. The Folder Carries Its Rule

A rule belongs to the folder it sorts, in that folder's `.MyOS/Sort.md`:

```md
# Sort
Pattern: {{YYYY}}/{{MM}}
DateSource: filename, modified
NewLevelFrom: 20 files
```

- **Templates prepare it:** `Templates/Standard/.../Rechnungen/.MyOS/Sort.md`. Nothing is
  filed inside a template (no data there); when the folder is born in a project, its
  `.MyOS` is copied along (as for every embryo), and the rule works there.
- **Any folder** inside a project can get a rule; outside projects there are none.
- The former form - one project-level `Sort.md` with `Root: /Pictures` - is replaced
  (nobody uses it yet).

## 3. Three Stages: Flat, Virtual, Real

A level of the structure is only created when the level above becomes hard to overlook.

- **Flat:** as long as the folder holds at most *N* files (`NewLevelFrom`, e.g. 20), they
  stay where they are.
- **Virtual:** Scope *shows* the files grouped into virtual year and month folders (faint,
  like embryos); nothing changes on disk. The x-ray view (`core/xray.py`) looks through
  small virtual folders like through real ones - with two invoices one simply sees the two
  files, not two faint folders with one file each.
- **Real:** when the folder holds more than *N* files, the first level becomes real:
  every file goes into its year folder, born when first needed. The next level follows the
  same rule inside each year: a year with more than *N* files gets real month folders;
  a year with six invoices stays without. Example: `2026` already has `03`, a May invoice
  arrives - `05` is born.

*N* is part of the rule, not of the window size: what is created on disk must be
predictable. No empty folders are ever created: folders are born when a file goes in,
never ahead by calendar.

Once created, a level stays: if invoices are deleted and a year keeps only three, its
folder remains. Only a folder emptied completely disappears, as born folders already do.

## 4. Filing Without Watching

MyOS does not depend on catching every file event (a watcher misses files while Scope is
elsewhere, and a debounce can swallow a second file). Instead it **catches up**: whenever
the folder is looked at (Scope, `myls`), when Scope starts, and once a day, MyOS checks
what is due and files it. This is idempotent: what was left last time is filed next time;
nothing gets lost.

Only files lying directly in the sorted folder (or in a real level's folder, for the next
level) are filed. What someone put into a subfolder of their own stays where it is.

## 5. Date Sources

The rule says where the date comes from, in this order (the first that gives one wins):

| Source | Meaning |
|---|---|
| `exif` | the photo's recording date (EXIF `DateTimeOriginal`, read with Pillow) |
| `filename` | a date in the file name (`2024-05-17`, `20240517`) |
| `frontmatter` | `date:` / `created:` in a Markdown file's front matter |
| `modified` | the file's modification time - last resort (after copying often the copy date) |

Photos: `exif, filename, modified`. Invoices: `filename, modified`. A late March invoice
arriving in May goes to March when its date comes from the name or the content.

## 6. Pattern Tokens

`{{YYYY}}`, `{{YY}}`, `{{MM}}`, `{{MMMM}}` (month name), `{{DD}}`, `{{ABC}}` (first letter
of the name). One date token per level; `..`, absolute fragments and separators inside a
token are rejected.

## 7. Trying Out a Rule

Virtual folders also serve to try out where a structure makes sense: with a rule in
place, Scope shows how the folder would look, before anything is created. Once one has
decided, the rule goes into the template; from then on new projects file by themselves.

## 8. Safety

- Sorting never executes file content.
- Path traversal is rejected; folders are created inside the sorted folder only.
- Name clashes: `rename` (default, "name (2).pdf"), `skip` or `error`.
- Self-moves are not taken for new arrivals.
- Filing follows the ACLs: files are only moved where the user may write.

## 9. Open

- The value of *N* per default (20 suggested).
- Whether the young files in a folder should keep a grace period before filing (an earlier
  idea: "invoices arrive within three months"); with the threshold, new files stay visible
  at the top while there are few, so it is left out for now.
- `myls`: show virtual levels (e.g. `2024/ (virtual)`).

## 10. Implementation

- `core/filing.py`: the rule (`read_rule`), dates (`date_of`: EXIF with Pillow, file name,
  front matter, modification time), the stages (`file_due` files what is due,
  `virtual_groups` / `virtual_listing` give the virtual folders), and helpers for Scope
  (`sorted_folder_for`, `sorted_folders`, `destination_for`).
- `ScopeApi`: a sorted folder (or one of its level folders) is filed when it is listed;
  `catch_up_filing_all` files a whole project tree (Scope: 3 s after the start and once a
  day, in the background; the listing is refreshed afterwards). After a move the target
  is filed at once; the move preview says where a file will go. Filing moves only where
  the ACLs allow writing; ACL rules follow filed files. `enable_sorting` gives the folder
  shown a rule ("Enable sorting").
- Listings show virtual folders (`isVirtual`, faint); one can open them (their content
  comes from `virtual_listing`), not drop into them, rename or delete them. The x-ray view
  sees through small virtual folders: their files then show where they really lie.
- The FUSE layer (`localBlueprintLayer`) shows the virtual level folders too; writing
  into one creates it.
- Removed: `core/sort.py`, `core/sort_runtime.py` (rules with `Root:` in the project's
  `Sort.md`, the watcher with its debounce, the name-only "EXIF"), the project-level
  `Sort.md` of the Desk service, and the "Sort in now" button.
