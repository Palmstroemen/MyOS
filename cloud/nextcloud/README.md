# MyOS for Nextcloud

`myacl sync` (cli/myacl.py, core/acl_nextcloud.py) copies a project's `.MyOS/ACLs.md` into a
Team folder with "advanced permissions". The app `myos_acl` closes the one gap Nextcloud
leaves: who may only work deep down gets read on the way there, and an entry created later
on that way would inherit that read. The app locks such entries the moment they are created,
moved or copied there.

## Install the app (Nextcloud admin, once)

Copy `myos_acl/` into the server's `custom_apps/` (owned by the web server user), then

    occ app:enable myos_acl

Needs the Team folders app (groupfolders). Tested with Nextcloud 32 and Team folders 20.1.

## What `myacl sync` needs on the server

- a Team folder with advanced permissions switched on, given to a group of everyone involved
- for the account that syncs: "manage advanced permissions" on that folder, and read on all of it
- an app password for that account (personal settings, Security)

## Test

`tests/test_myos_acl_app.py` runs against a test instance only (it changes the Team folder's
rules); see its docstring. Without `MYOS_NC_TEST_URL` it is skipped.

## The row of MyOS folders

Above the file list the app shows the MyOS folders of the current folder, born ones in full
colour, embryos pale; clicking an embryo gives birth to it as MyOS does (the folder, then the
files and hidden folders of that template level). Born MyOS folders leave the list below
(Nextcloud counts them as "hidden" there). Embryos show only where one may create.

`myacl sync` writes per project `.MyOS/Embryos.json` (the template tree and, per embryo, what
its birth copies, with a hash per file) and uploads those files to `.MyOS/Embryos/<embryo>/`
(core/cloud_embryos.py). Everyone with rights in the project may read these two, nothing else
of `.MyOS`. The browser takes the nearest manifest up the path and copies on the server.

The browser part is `src/main.js`, built to `js/myos_acl-main.js` (committed, so installing
needs no Node):

    cd cloud/nextcloud/myos_acl && npm install && npm run build
