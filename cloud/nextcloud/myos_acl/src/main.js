/**
 * MyOS folders in the Files app: above the file list one row with the MyOS folders of the
 * current folder, always together - born ones in full colour, embryos (suggested, not yet
 * created) pale. The born ones leave the list below, so it holds what the user made.
 *
 * Which folders a level suggests comes from .MyOS/Embryos.json at the project root (written
 * by MyOS, the one place that resolves templates): {"version": 1, "tree": {name: subtree}}.
 * The nearest one up the path governs, as a subproject's own does.
 */
import { getRequestToken } from '@nextcloud/auth'
import { FileListFilter, Header, registerFileListFilter, registerFileListHeaders } from '@nextcloud/files'
import { t } from '@nextcloud/l10n'

const APP = 'myos_acl'
const EMBRYO_OPACITY = 0.4 // as Scope's default for suggested folders

// The folder shown and what MyOS says about it.
const state = { folder: null, names: [], born: new Set(), el: null }
const manifests = new Map() // DAV URL of a folder -> Promise of its tree, or null

function manifest(source) {
	if (!manifests.has(source)) {
		manifests.set(source, fetch(source + '/.MyOS/Embryos.json', {
			headers: { requesttoken: getRequestToken() ?? '' },
			credentials: 'same-origin',
		}).then(response => response.ok ? response.json() : null)
			.then(data => (data && data.version === 1 && typeof data.tree === 'object') ? data.tree : null)
			.catch(() => null))
	}
	return manifests.get(source)
}

/** The names of the MyOS folders of folder: the children of its node in the nearest tree. */
async function myosNames(folder) {
	const userRoot = folder.source.slice(0, folder.source.length - folder.path.length).replace(/\/$/, '')
	const parts = folder.path.split('/').filter(Boolean)
	for (let depth = parts.length; depth >= 0; depth--) {
		const base = userRoot + parts.slice(0, depth).map(p => '/' + encodeURIComponent(p)).join('')
		const tree = await manifest(base)
		if (!tree) {
			continue
		}
		let node = tree
		for (const part of parts.slice(depth)) {
			node = node?.[part]
		}
		return node && typeof node === 'object'
			? Object.keys(node).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
			: []
	}
	return []
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
	return (state.folder.path.replace(/\/$/, '') + '/' + name)
}

function open(name) {
	window.OCP.Files.Router.goToRoute(null, { view: 'files' }, { dir: childPath(name) })
}

/** Prototype birth: the folder only; the template's files and .MyOS come with the next step. */
async function birth(name) {
	const response = await fetch(state.folder.source.replace(/\/$/, '') + '/' + encodeURIComponent(name), {
		method: 'MKCOL',
		headers: { requesttoken: getRequestToken() ?? '' },
		credentials: 'same-origin',
	})
	if (!response.ok) {
		throw new Error(`MKCOL ${name}: ${response.status}`)
	}
	open(name)
}

function render() {
	const el = state.el
	if (!el) {
		return
	}
	el.replaceChildren()
	if (state.names.length === 0) {
		return
	}
	const label = document.createElement('span')
	label.className = 'myos-row__label'
	label.textContent = t(APP, 'MyOS folders')
	el.append(label)
	for (const name of state.names) {
		const born = state.born.has(name)
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
	state.names = []
	render()
	const names = await myosNames(folder)
	if (state.folder === folder) {
		state.names = names
		render()
		filter.changed()
	}
}

class MyOSFolders extends FileListFilter {
	constructor() {
		super('myos-folders', 0)
	}

	/** Notes which MyOS folders are born, and takes them out of the list (they are in the row). */
	filter(nodes) {
		const folder = state.folder
		if (!folder) {
			return nodes
		}
		const here = nodes.filter(node => node.dirname === folder.path && node.type === 'folder').map(node => node.basename)
		const born = new Set(here.filter(name => state.names.includes(name)))
		if (born.size !== state.born.size || [...born].some(name => !state.born.has(name))) {
			state.born = born
			render()
		}
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
