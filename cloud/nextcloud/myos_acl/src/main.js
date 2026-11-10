/**
 * MyOS folders in the Files app: above the file list one row with the MyOS folders of the
 * current folder, always together - born ones in full colour, embryos (suggested, not yet
 * created) pale. The born ones leave the list below, so it holds what the user made.
 *
 * Which folders a level holds, and what a birth creates and copies, the MyOS core answers
 * (cloud/service/level.py, through myos_acl's CoreController): born ones the user may read,
 * embryos where the user may create, as Scope with ACLs enforced. The browser shows that and
 * gives birth with the user's own rights - Nextcloud checks them once more.
 */
import { getCurrentUser, getRequestToken } from '@nextcloud/auth'
import { FileListFilter, Header, getNavigation, registerFileListFilter, registerFileListHeaders } from '@nextcloud/files'
import { t } from '@nextcloud/l10n'
import { generateRemoteUrl } from '@nextcloud/router'
import { askCore } from './core.js'
import { registerPerspectives } from './lens.js'

const APP = 'myos_acl'
const EMBRYO_OPACITY = 0.4 // as Scope's default for suggested folders

// The folder shown and the core's answer for it: [{name, born}], null outside MyOS.
const state = { folder: null, folders: null, el: null }

function davUrl(path) {
	const root = generateRemoteUrl('dav/files/' + encodeURIComponent(getCurrentUser().uid))
	return root.replace(/\/$/, '') + path.split('/').filter(Boolean).map(p => '/' + encodeURIComponent(p)).join('')
}

function dav(method, url, headers = {}) {
	return fetch(url, { method, headers: { requesttoken: getRequestToken() ?? '', ...headers }, credentials: 'same-origin' })
}

const style = `
.myos-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 6px 12px; }
.myos-row:empty { display: none; }
.myos-row__label { color: var(--color-text-maxcontrast); font-size: 0.85em; margin-inline-end: 6px; }
.myos-folder { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
	border: 1px solid var(--color-border); border-radius: var(--border-radius-pill, 16px);
	background: var(--color-main-background); color: var(--color-main-text); cursor: pointer; }
.myos-folder:hover { background: var(--color-background-hover); }
.myos-folder--embryo { opacity: ${EMBRYO_OPACITY}; border-style: dashed; }
.myos-folder--embryo:hover { opacity: 0.7; }
.myos-folder svg { width: 18px; height: 18px; fill: var(--color-primary-element); }
`
const folderIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>'

function childPath(name) {
	return state.folder.path.replace(/\/$/, '') + '/' + name
}

function open(name) {
	window.OCP.Files.Router.goToRoute(null, { view: 'files' }, { dir: childPath(name) })
}

async function must(response, what) {
	if (!response.ok && response.status !== 405) { // 405: the folder is there already
		throw new Error(`${what}: ${response.status}`)
	}
}

/** Birth as the core says (as MyOS' BirthClinic does): the folders, then the copies. */
async function birth(name) {
	const { status, data } = await askCore('birth', childPath(name))
	if (status !== 200 || !data) {
		throw new Error(`birth ${name}: ${status}`)
	}
	for (const folder of data.create) {
		await must(await dav('MKCOL', davUrl(folder)), `MKCOL ${folder}`)
	}
	for (const copy of data.copy) {
		await must(await dav('COPY', davUrl(copy.from), { Destination: davUrl(copy.to), Overwrite: 'F' }), `COPY ${copy.to}`)
	}
	open(name)
}

function render() {
	const el = state.el
	if (!el) {
		return
	}
	el.replaceChildren()
	const folders = state.folders ?? []
	if (folders.length === 0) {
		return
	}
	const label = document.createElement('span')
	label.className = 'myos-row__label'
	label.textContent = t(APP, 'MyOS folders')
	el.append(label)
	for (const { name, born } of folders) {
		const button = document.createElement('button')
		button.type = 'button'
		button.className = 'myos-folder' + (born ? '' : ' myos-folder--embryo')
		button.title = born ? name : t(APP, 'Suggested folder: click to create it')
		button.innerHTML = folderIcon
		button.append(document.createTextNode(name))
		button.addEventListener('click', () => (born ? open(name) : birth(name)).catch(error => console.error('MyOS', error)))
		el.append(button)
	}
}

async function show(folder) {
	state.folder = folder
	state.folders = null
	render()
	const { status, data } = await askCore('level', folder.path).catch(() => ({ status: 0 }))
	if (state.folder === folder) {
		state.folders = status === 200 ? data.folders : null
		render()
		filter.changed()
	}
}

class MyOSFolders extends FileListFilter {
	constructor() {
		super('myos-folders', 0)
	}

	/** Takes the born MyOS folders out of the list (they are in the row). */
	filter(nodes) {
		const folder = state.folder
		if (!folder || getNavigation().active?.id !== 'files') {
			return nodes // the row is only in "All files"
		}
		const born = new Set((state.folders ?? []).filter(f => f.born).map(f => f.name))
		return nodes.filter(node => !(node.dirname === folder.path && node.type === 'folder' && born.has(node.basename)))
	}

	changed() {
		this.filterUpdated()
	}
}

const filter = new MyOSFolders()

const sheet = document.createElement('style')
sheet.textContent = style
document.head.append(sheet)

registerFileListFilter(filter)
registerFileListHeaders(new Header({
	id: 'myos-folders',
	order: 0,
	enabled: (folder, view) => view.id === 'files',
	render(el, folder) {
		state.el = document.createElement('div')
		state.el.className = 'myos-row'
		el.append(state.el)
		show(folder)
	},
	updated(folder) {
		show(folder)
	},
}))

registerPerspectives()
