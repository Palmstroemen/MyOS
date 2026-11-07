/**
 * MyOS folders in the Files app: above the file list one row with the MyOS folders of the
 * current folder, always together - born ones in full colour, embryos (suggested, not yet
 * created) pale. The born ones leave the list below, so it holds what the user made.
 *
 * Which folders a level suggests, and what a birth copies, comes from .MyOS/Embryos.json at
 * the project root, written by myacl sync (core/cloud_embryos.py: MyOS is the one place that
 * resolves templates): {"version": 1, "tree": {name: subtree}, "births": {embryo: {"dirs":
 * [...], "files": {file: sha256}}}}, the files below .MyOS/Embryos/<embryo>/. The nearest one
 * up the path governs, as a subproject's own does.
 */
import { getCurrentUser, getRequestToken } from '@nextcloud/auth'
import { FileListFilter, Header, Permission, registerFileListFilter, registerFileListHeaders } from '@nextcloud/files'
import { t } from '@nextcloud/l10n'
import { generateRemoteUrl } from '@nextcloud/router'

const APP = 'myos_acl'
const EMBRYO_OPACITY = 0.4 // as Scope's default for suggested folders

// The folder shown and what MyOS says about it: its project (DAV URL) and its path there.
const state = { folder: null, level: null, born: new Set(), el: null }
const manifests = new Map() // DAV URL of a folder -> Promise of its manifest, or null

function davUrl(path) {
	const root = generateRemoteUrl('dav/files/' + encodeURIComponent(getCurrentUser().uid))
	return root.replace(/\/$/, '') + path.split('/').filter(Boolean).map(p => '/' + encodeURIComponent(p)).join('')
}

function dav(method, url, headers = {}) {
	return fetch(url, { method, headers: { requesttoken: getRequestToken() ?? '', ...headers }, credentials: 'same-origin' })
}

function manifest(url) {
	if (!manifests.has(url)) {
		manifests.set(url, dav('GET', url + '/.MyOS/Embryos.json')
			.then(response => response.ok ? response.json() : null)
			.then(data => (data && data.version === 1 && typeof data.tree === 'object') ? data : null)
			.catch(() => null))
	}
	return manifests.get(url)
}

/**
 * The MyOS level of folder: {project, rel, names, births} - the nearest manifest up the path,
 * folder's path below that project, and the names of its node in the tree; null outside.
 */
async function myosLevel(folder) {
	const parts = folder.path.split('/').filter(Boolean)
	for (let depth = parts.length; depth >= 0; depth--) {
		const project = davUrl(parts.slice(0, depth).join('/'))
		const data = await manifest(project)
		if (!data) {
			continue
		}
		const below = parts.slice(depth)
		let node = data.tree
		for (const part of below) {
			node = node?.[part]
		}
		const names = node && typeof node === 'object'
			? Object.keys(node).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
			: []
		return { project, rel: below.join('/'), names, births: data.births ?? {} }
	}
	return null
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

/**
 * Birth as in MyOS (BirthClinic): the folder, then what the template holds on that level -
 * its files and hidden folders such as .MyOS - copied on the server from the project's
 * .MyOS/Embryos/<embryo>/. Visible subfolders stay embryos.
 */
async function birth(name) {
	const { project, rel, births } = state.level
	const embryo = rel ? `${rel}/${name}` : name
	const target = davUrl(childPath(name))
	await must(await dav('MKCOL', target), `MKCOL ${name}`)
	const { dirs = [], files = {} } = births[embryo] ?? {}
	const encoded = path => path.split('/').map(encodeURIComponent).join('/')
	for (const dir of dirs) {
		await must(await dav('MKCOL', `${target}/${encoded(dir)}`), `MKCOL ${dir}`)
	}
	const source = `${project}/.MyOS/Embryos/${encoded(embryo)}`
	for (const file of Object.keys(files)) {
		await must(await dav('COPY', `${source}/${encoded(file)}`, {
			Destination: `${target}/${encoded(file)}`,
			Overwrite: 'F',
		}), `COPY ${file}`)
	}
	open(name)
}

function render() {
	const el = state.el
	if (!el) {
		return
	}
	el.replaceChildren()
	// Embryos only where one may create (as Scope with ACLs enforced); the born ones always.
	const mayCreate = Boolean(state.folder.permissions & Permission.CREATE)
	const names = (state.level?.names ?? []).filter(name => mayCreate || state.born.has(name))
	if (names.length === 0) {
		return
	}
	const label = document.createElement('span')
	label.className = 'myos-row__label'
	label.textContent = t(APP, 'MyOS folders')
	el.append(label)
	for (const name of names) {
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
	state.level = null
	render()
	const level = await myosLevel(folder)
	if (state.folder === folder) {
		state.level = level
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
		const born = new Set(here.filter(name => state.level?.names.includes(name)))
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
