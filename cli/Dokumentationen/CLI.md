# **MyOS CLI Overview (Draft)**

## **myls**
List files with MyOS-aware views.

Examples:
- `myls .`
- `myls --extended`
- `myls --tags`
- `myls --roentgen 10`

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

## **myedit**
Open a config section in your editor.

Examples:
- `myedit tags .`
- `myedit templates /path/to/project`
- `myedit acls /path/to/project`
