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

## The MyOS core next to Nextcloud (first piece: the lenses)

The core runs as its own container (`cloud/service/`, see "Designdocument MyOS Core
Service.md"). It reads the Team folder with the service account into a shadow tree (folders
and `.MyOS` files) and rebuilds it when the folder's ETag changes. `myos_acl` passes
`GET /ocs/v2.php/apps/myos_acl/api/v1/lens?path=` on with the logged-in account; the
browser never talks to the container. The project's `.MyOS` must lie in the Team folder
(sync client or browser), with `Nextcloud.md` naming the accounts.

    docker buildx build --load -f cloud/service/Dockerfile -t myos-core:dev .   # repo root
    docker network create myos-net && docker network connect myos-net <nextcloud container>
    docker run -d --name myos-core --network myos-net --env-file core.env myos-core:dev
    occ config:system:set trusted_domains <n> --value=<nextcloud container>
    occ config:app:set myos_acl core_url --value=http://myos-core:8080
    occ config:app:set myos_acl core_secret --sensitive --value=<MYOS_CORE_SECRET>

After each change of the Team folder the core does what `myacl sync` does
(core/nextcloud_sync.py) with the service account: a folder made later gets its rights from
`ACLs.md` within seconds, and an `ACLs.md` edited in the cloud changes the rules - unless it
leaves no one who may change the rights (then most likely broken: nothing is sent).
`myacl sync` from a desktop stays possible and does the same.

In Files the view "Perspectives" (left bar, `src/lens.js`) shows the turned tree:
departments, their folders, the shelf with the projects one may read, then the real
folders and files - opening, downloading, renaming and deleting act on the real ones. A
folder opens at its turned path, so the breadcrumbs stay in the lens. Where the department
folder is not born in a project, the project's own folder is shown read-only (saving through
a lens comes later). The view goes again for an account the core does not know.

`core.env` (mode 600): `MYOS_CORE_SECRET` (24 characters at least), `MYOS_NC_URL`
(`http://<nextcloud container>`), `MYOS_NC_USER`, `MYOS_NC_PASSWORD` (an app password of the
service account: a person of the role Admin), `MYOS_NC_FOLDER`, optionally `MYOS_SHADOW_POLL`
(seconds, default 10). No port is published. After updating the app: `occ app:disable
myos_acl && occ app:enable myos_acl`, so Nextcloud reads its new routes.

## The row of MyOS folders

Above the file list the app shows the MyOS folders of the current folder, born ones in full
colour, embryos pale; clicking an embryo gives birth to it as MyOS does (the folder, then the
files and hidden folders of that template level). Born MyOS folders leave the list below
(Nextcloud counts them as "hidden" there). Embryos show only where one may create.

`myacl sync` uploads per project a folder per embryo, `.MyOS/Embryos/<embryo>/`, holding what
its birth copies (the files and hidden folders of that template level; its visible
subfolders are the deeper embryos), and `.MyOS/Embryos.json` (the template tree and a hash
per file, the sync's bookkeeping) (core/cloud_embryos.py). Everyone with rights in the
project may list `.MyOS/Embryos/`, each embryo's folder only who may read the folder it
becomes, as Scope shows embryos: who may do nothing in `/00_Admin` sees neither that embryo
nor its template. Nothing else of `.MyOS` comes with it. What manages rights and the sync in
any `.MyOS` (`ACLs.md`, `ACLs-history`, `Nextcloud.md`, `Embryos.json`, `Embryos/`) may only
be written by who has `change` on that `ACLs.md` - so the account that syncs needs it too.
The browser takes the nearest project up the path, lists the embryos it may read there and
copies on the server.

The browser part is `src/main.js`, built to `js/myos_acl-main.js` (committed, so installing
needs no Node):

    cd cloud/nextcloud/myos_acl && npm install && npm run build
