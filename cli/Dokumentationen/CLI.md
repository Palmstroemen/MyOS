# **MyOS CLI Overview (Draft)**

## **myls**
List files with MyOS-aware views.

Examples:
- `myls .`
- `myls --extended`
- `myls --tags`
- `myls --roentgen` (x-ray: files of small folders, while the terminal's height suffices; `--roentgen 10`: 10 lines). Files seen through show where they lie: `r1.pdf   (in Rechnungen/2024)`

---

## **myproject**
Project management.

Examples:
- `myproject create /path/to/folder`
- `myproject create --new /path/to/new-folder`

---

## **myexport**
Export a subtree from a project.

Examples:
- `myexport /path/inside/project --out /tmp/export`
- `myexport /path/inside/project --out /tmp/export --zip`

---

## **myimport**
Import a package into a target location.

Examples:
- `myimport /tmp/export/package`
- `myimport /tmp/export/package --target /path/to/target --mode adopt --conflict merge`

---

## **myfilter**
Filter utilities (list and resolve).

Examples:
- `myfilter list .`
- `myfilter resolve .`
- `myfilter resolve . --manual /path/to/Filter.md`

---

## **mytag**
Tag utilities (xattr-based).

Examples:
- `mytag list file.txt`
- `mytag add file.txt dringend`
- `mytag set file.txt wichtig=60`
- `mytag remove file.txt dringend`
- `mytag clear file.txt`

---

## **myacl**
ACLs: who may do what, and every rule of a project. Read-only; edit rules with `myedit acl` or in Scope/PostFix. With `MYOS_ACL_MODE=enforce` only people who may read ACLs.md see them.

Examples:
- `myacl show Finanz/Archiv` (roles and people with their rights here; per role `here` or `from /Finanz`: the folder whose rule decides)
- `myacl check Anna Finanz delete` (prints yes/no; exit 0 = allowed, 1 = not, 2 = error)
- `myacl check Anna Finanz` (all rights of Anna there)
- `myacl rules .` / `myacl rules . --json` (every rule, `## Folder` rules resolved into each subproject, paths as written in ACLs.md, `[]` = `none`; the input for adapters, e.g. to a cloud)
- `myacl sync --plan .` (the rules a Nextcloud Team folder with "advanced permissions" should hold, per person; settings in `.MyOS/Nextcloud.md`, see below; no network)
- `myacl sync --dry-run .` (reads the Team folder and its rules over WebDAV and shows what would change: `+` new, `~` changed, `-` goes because it is not from ACLs.md; sends nothing. Login from `MYOS_NEXTCLOUD_USER` and `MYOS_NEXTCLOUD_PASSWORD`, best an app password; the account needs "manage advanced permissions" and should be able to read the whole folder)
- `myacl sync .` (shows the same, asks, sends the rules path by path, deepest first, and reads them back to check; `--yes` sends without asking, needed without a terminal. Rules not from ACLs.md go. Needs `group:`; with the server app `cloud/nextcloud/myos_acl` new entries on the way are locked at once, see `cloud/nextcloud/README.md`. Uploads each project's embryos first - `.MyOS/Embryos.json` and the files a birth copies - for the row of MyOS folders in the Files app; everyone with rights in the project may read them)

`.MyOS/Nextcloud.md`:
```
# Nextcloud
url: https://cloud.example.org
folder: Projekte         (the Team folder, as it shows in the account's files)
group: Projekte          (the groups the Team folder is given to, comma-separated: locked out at the root)

# Accounts
Anna Huber: anna.h       (person in # Users: Nextcloud account; people without one get no rules)
```

---

## **myedit**
Open a config section in your editor.

Examples:
- `myedit tags .`
- `myedit templates /path/to/project`
- `myedit acls /path/to/project`

---

## **myperspectivefs**
Mount the flipped perspective FUSE adapter as a separate filesystem.

Examples:
- `myperspectivefs --project-root /data/Projekte --mount-point /mnt/myos-structure --foreground`
- `myperspectivefs --project-root /data/Projekte --mount-point /mnt/myos-structure --start-real-path /data/Projekte/ProjektA/kommunikation/email`

Notes (MVP):
- v1 supports only `--perspective flipped`
- no small-project fallback behavior yet
- adapter is thin: mapping semantics come from the core perspective resolver
