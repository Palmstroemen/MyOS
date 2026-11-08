# MyOS on Nextcloud - The Core as a Service (decided 2026-11-08)

## 1. The Goal

Someone with a Nextcloud - on Linux, Windows or a Mac, it does not matter, they only use the
browser - installs MyOS as an add-on next to it and gets MyOS there: projects, embryos and
births, ACLs with inheritance, perspectives, tags. Not a look-alike: the same behaviour as on
the desktop, because the same code decides.

## 2. The One Rule

**There is one engine: the MyOS core (Python).** Nothing of MyOS' logic is rebuilt in PHP or
JavaScript - not the template resolution, not the inheritance of `ACLs.md` or `Templates.md`,
not the perspective resolver, not the tags. PHP and JavaScript only

- show what the core answers,
- pass on what the user does and what changes in the files,
- and enforce what the core decided (Nextcloud's own ACLs, the lock of `myos_acl`).

Whatever a test can only check in JavaScript or PHP is suspect: if it encodes a MyOS rule, it
belongs in the core.

## 3. Where We Stand (commit 1e05deb)

MyOS runs on the desktop as a compiler and the cloud gets the result: `myacl sync` reads a
local copy, sets real Team folder rules and uploads `Embryos.json` with the template files.
The rights are real, Nextcloud enforces them. But the logic only runs at sync time:

| In Nextcloud ...                 | today                                                     |
|----------------------------------|-----------------------------------------------------------|
| read, write, lock                | real, computed by MyOS                                    |
| a new folder in the browser      | locked at once, its rights only at the next sync          |
| `ACLs.md` edited in the browser  | no effect until a sync from a local copy                  |
| birth of an embryo               | the browser copies a list MyOS computed beforehand        |
| perspectives, tags, filters      | missing                                                   |

Kept as they are: `core/acl_nextcloud.py` (the planner), `core/nextcloud_dav.py` (rules and
files over WebDAV), `core/cloud_embryos.py` (what a birth copies), the lock in `myos_acl`
(the safety net for the moment between a change and the core's answer), the row in Files.
Replaced: the static `Embryos.json` and the payload as the browser's source.

## 4. The Picture

    Browser (Files app)                  Nextcloud server                   MyOS container
    ───────────────────                  ────────────────                   ──────────────
    row "MyOS folders",       ──OCS──▶   myos_acl (PHP)          ──HTTP──▶  myos-core
    perspectives view,                   - proxies the API,                 - shadow tree
    tags                                   with the user's id               - Blueprint, ACLAuthorizer,
                                         - forwards file events               perspective resolver, tags
                              ◀──────    - locks new entries                - applies rules (WebDAV,
                                                                              service account)

- **myos-core** is one Docker image: the MyOS core plus a small HTTP API. It is the CLI's
  logic as an API, not a second implementation.
- **myos_acl** (our PHP app) becomes the bridge: routes `/apps/myos_acl/api/...` to the core
  (shared secret, the logged-in user's id passed along), and forwards Nextcloud's file events
  (created, renamed, copied, deleted, written) for Team folders the core manages.
- **The browser** talks only to `myos_acl`, never to the container directly.

## 5. The Shadow Tree

The core works on a filesystem (`Path`); Nextcloud's storage may be local, S3 or anything.
Instead of rewriting the core for WebDAV, the container keeps a **shadow tree** per managed
Team folder: every folder (empty), every `.MyOS` file, `Templates/` with its files. No user
documents. That is all Blueprint, ACLAuthorizer and the perspective resolver read.

- Built at start from a WebDAV walk (as `NextcloudDAV.tree()` does today), then kept current
  by the forwarded events; a periodic ETag check catches what an event missed.
- The shadow is a cache, never a source: on doubt it is rebuilt.
- The source of truth is the Team folder itself. A desktop MyOS with the sync client sees the
  same `ACLs.md`; `myacl sync` from the desktop becomes optional.

## 6. Who Acts with Which Rights

- **The core decides, the user acts with their own rights.** A birth: the core answers what
  to create and copy (from the live templates, by the same code as `BirthClinic`); the
  browser does it with the user's session, so Nextcloud checks the user's rights as for any
  other action. The core never writes documents on a user's behalf.
- **The service account sets rules.** One account with "Manage advanced permissions" on the
  Team folder (a person of the role Admin, as `myacl sync` needs today) applies the rules the
  core computes, right after the event that needs them. A newborn folder gets its rights in
  seconds, not at the next sync.
- **A template is like a form at an office**: whoever may file the application may see the
  blank form. So the template of an embryo is readable exactly for those who may give birth
  to it - who may create at the place where it would be born (by `ACLs.md`, with the folder
  rules of the embryo's path). Whoever may do nothing there sees neither the embryo nor its
  template (e.g. `/00_Admin` for someone outside the role Admin). The birth then copies with
  the user's own rights; there are no files a user owns afterwards but was not allowed to
  read before. Built into `myacl sync` already (2026-11-08): each embryo's folder in
  `.MyOS/Embryos/` is readable for who may read the folder it becomes, as Scope shows an
  embryo (read there); births need create on top, which Nextcloud checks.
- `myos_acl` passes the user's id; the core trusts only that header and only with the shared
  secret. The container is reachable from the Nextcloud server alone.

## 7. Hosting

One image, two ways to run it, the same code:

1. **Sidecar (first):** `docker compose` next to Nextcloud; the admin sets the core's URL and
   secret in `myos_acl`. Needs Docker on the server and `myos_acl`, nothing else. Works for
   the friend's Nextcloud 32.0.1 if he can run a container there.
2. **ExApp (later):** packaged for AppAPI (shipped with Nextcloud since 30.0.1), installed
   from the app store; the admin needs a deploy daemon (HaRP is the recommended one for 32).
   Then AppAPI does what the bridge does by hand. To be checked when we get there: whether
   file events for ExApps go through webhooks (`nc_py_api` 0.20 dropped its events listener
   for `nc_py_api.webhooks`) and how scripts get into the Files app.

The GMXtec is only our test host; nothing depends on it.

## 8. Steps

1. **Core service, births and rights live** - the container with the shadow tree and the API
   `GET level?path=` (MyOS folders of a level: born, embryos, may create) and
   `GET birth?path=` (what the birth creates and copies); `myos_acl` proxies both and
   forwards events; the core sets the rules after each event. The row in Files asks the API
   instead of listing `.MyOS/Embryos/`, as the first piece of the small Scope (9.4): the
   web component, with the Files app as its first shell. Done when: the integration test births a folder as Lisa and
   the folder has its `ACLs.md` rights without a sync; editing `ACLs.md` in the cloud changes
   the rules.
2. **Perspectives** - an own view in Files (left bar), the resolver in the core answers what
   a lens shows; saving through a lens: the core maps the path, the browser writes there.
3. **Tags and filters** - onto Nextcloud's collaborative tags where they fit.
4. **ExApp packaging.**

## 9. Nextcloud Is the First, Not the Only One - the Whole Picture

Next could be Obsidian, OneDrive, Google Drive/Docs, Dropbox, Synology, OpenCloud. So what
we build now is cut along that line from the start.

    ┌──────────────── Docker image (the same everywhere) ────────────────┐
    │  MyOS core: Blueprint, ACLs, perspective resolver, tags            │
    │  API in MyOS terms (embryos, births, rights, lenses, projects)     │
    │  adapters: nextcloud | synology | onedrive | ...                   │
    │            (shadow tree + changes, rights translated)              │
    │  the small Scope as a web component                                │
    └────────────────────────────────────────────────────────────────────┘
              ▲                                       ▲
     a thin shell per platform              the platform's API / WebDAV
     (Files app, Obsidian plugin, ...)

### 9.1 The Package: One Docker Image

Docker packs the core with Python, its libraries and the web files into one image that runs
alike wherever a container runtime runs. Which adapter is active is a setting, not another
image. Docker settles the packing, not the place:

| Platform                                   | Where the image runs                                      |
|--------------------------------------------|-----------------------------------------------------------|
| Nextcloud, OpenCloud (own server), Synology (Container Manager) | right beside it                      |
| OneDrive, Google Drive, Dropbox            | elsewhere (at home, a NAS, a rented server); one cannot upload code to them, the image talks to their API |
| Obsidian                                   | no server: the core runs on the desktop as today, next to the vault |

### 9.2 No FUSE in the Cloud

FUSE does not sit on top of a filesystem: it is the operating system's interface through
which a program presents an invented filesystem whose content it supplies (Linux built in;
macFUSE or FUSE-T on macOS; WinFsp or Dokan on Windows, similar but not the same). In a
container it needs `/dev/fuse` and `SYS_ADMIN`, which many hosts forbid.

The cloud does not need it. The drive is one way to show perspectives - for desktop
programs, whose save dialogs understand only paths. In the cloud the save dialog is our own
plugin, which asks the core directly what a lens shows and where a file really belongs. The
shadow tree is a plain folder. So the perspective logic must stay apart from the drive
(`core/perspective.py` and the resolver on one side, `core/perspective_fuse.py` on the
other); how cleanly they are apart today is checked in step 2.

### 9.3 Small Adapters, Three Parts

- **The core knows no platform.** It reads a shadow tree and answers in MyOS terms. The
  service's API speaks these terms, never a platform's.
- **Files**: build and keep the shadow tree (walk, then events or polling) and carry out
  what the user does through the platform (WebDAV here; Graph API for OneDrive, Drive API,
  Dropbox API, the vault's folder for Obsidian). The adapter never copies users' documents:
  syncing them is the platform's job (its sync client, its web app).
- **Rights**: map the rights the core computes to what the platform enforces, and report
  what it cannot hold - as `core/acl_nextcloud.py` does with patterns and `change`.
  Platforms differ most here: Nextcloud's advanced permissions and Synology's Windows-like
  ACLs hold MyOS' "nearest rule wins"; OneDrive, Google Drive and Dropbox only share items
  (rights add up, nothing can be taken away deeper), so there the adapter must refuse or
  approximate, never pretend.
- Today the Nextcloud parts live in `core/` (`acl_nextcloud.py`, `nextcloud_dav.py`); with
  step 1 they move into the Nextcloud adapter, so `core/` keeps no platform code.

### 9.4 The Small Scope: Built Once, a Thin Shell per Platform

The browser side - the transparent folders, creating a project, births, perspectives - is
built once as a web component (HTML/JS) that talks only to the core's API. Per platform a
thin shell embeds it where that platform lets one in:

| Platform                         | Where the small Scope appears                                 |
|----------------------------------|---------------------------------------------------------------|
| Nextcloud                        | in the Files app (as the row today)                           |
| Obsidian                         | a plugin in its file explorer (Obsidian is a browser itself)  |
| Synology                         | an own DSM app                                                |
| OneDrive (personal), Google Drive, Dropbox | their file browsers take no plugins: an own web page served by the image, showing their files through their API. OneDrive for Business could go through SharePoint extensions, Google Drive only as a narrow side panel |

The desktop stays as it is: the drive with FUSE, Scope, SunTree, PostFix.

## 10. Open Questions

- Events from the sync client and `occ files:scan` arrive the same way? To be checked.
- Which events are enough to keep the shadow current, and how fast the ETag check must be.
- Rights of the user who edits `ACLs.md` in the browser: the core applies only what that
  user's `change` allows (as in MyOS); what does the user see when part is refused?
