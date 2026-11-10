/**
 * The view "Perspectives" in the Files app: the projects seen from a department, the turned
 * path of MyOS (/04_Finanz/Projekte/Job = Projekte/Job/04_Finanz). What a turned path stands
 * for comes from the MyOS core (cloud/service/lens.py, through myos_acl's CoreController):
 * the virtual levels - departments, their folders, the shelf with the projects one may read -
 * or the real folder, which is listed here over WebDAV with the user's rights. Opening,
 * downloading, renaming and deleting act on the real files.
 *
 * The Files app opens a folder at its real path (node.path); inside this view a folder opens
 * at its turned path instead, so the breadcrumbs stay in the lens.
 *
 * Saving through a lens: where a project's department folder is not born, the lens shows the
 * project's own folder, read-only, and above it the department folder as an embryo. A click
 * bears it (with every missing level, as the core plans it: bear), dropping files on it bears
 * it and puts them in - "dropping into the lens creates the canonical target".
 */
import { getCurrentUser } from '@nextcloud/auth'
import { emit } from '@nextcloud/event-bus'
import { DefaultType, FileAction, FileType, Folder, Header, Permission, View, getNavigation, registerFileAction, registerFileListHeaders } from '@nextcloud/files'
import { defaultRemoteURL, defaultRootPath, getClient, getDefaultPropfind, resultToNode } from '@nextcloud/files/dav'
import { t } from '@nextcloud/l10n'
import { askCore, carryOut, folderIcon, upload } from './core.js'

const APP = 'myos_acl'
const VIEW = 'myos-perspectives'
const VIRTUAL = '/.myos-perspectives' // under the user's root: no such folder, only keys for the store

const glassesIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 10c-.5 0-.8.4-.8.9l.5 3C2.8 14.5 3.4 15 4 15h3c.6 0 1.4-.6 1.5-1.2l1-3.2c.2-.3 0-.6-.5-.6H3m4 7H4c-1.6 0-3-1.3-3.2-2.9l-.5-3C0 9.4 1.3 8 3 8h6c.9 0 1.7.4 2.1 1l.3.5c.4-.1.8-.1 1.2 0l.3-.5c.4-.6 1.2-1 2.1-1h6c1.7 0 3 1.4 2.7 3.1l-.5 3.1c-.2 1.5-1.6 2.8-3.2 2.8h-3c-1.6 0-3.1-1.2-3.5-2.7l-.9-2.7c-.4-.3-.9-.3-1.3 0l-.9 2.8C10.1 15.8 8.6 17 7 17m8-7c-.5 0-.6.4-.5.7l1 3.1c.2.6.9 1.2 1.5 1.2h3c.6 0 1.2-.5 1.3-1.1l.5-3.1c0-.4-.3-.8-.8-.8h-6z"/></svg>'

// Source of a folder shown in this view -> its turned path.
const turned = new Map()
// Source of a project's folder shown for its unborn department folder -> {path, department, project}.
const unborn = new Map()
const header = { el: null }
let nextVirtualId = -1
const virtualIds = new Map()

function join(path, name) {
	return path.replace(/\/$/, '') + '/' + name
}

/** A level that exists only in the lens (a department, the shelf, a project on it). */
function virtualFolder(path) {
	const source = defaultRemoteURL + defaultRootPath + VIRTUAL + path.replace(/\/$/, '')
	if (!virtualIds.has(source)) {
		virtualIds.set(source, nextVirtualId--)
	}
	turned.set(source, path)
	return new Folder({
		id: virtualIds.get(source),
		source,
		root: defaultRootPath,
		owner: getCurrentUser()?.uid ?? null,
		permissions: Permission.READ,
		displayname: path.split('/').filter(Boolean).pop() ?? t(APP, 'Perspectives'),
	})
}

async function realContents(path, answer) {
	const real = answer.place.replace(/\/$/, '') + answer.real
	const client = getClient()
	const options = { details: true, data: getDefaultPropfind() }
	const [self, entries] = await Promise.all([
		client.stat(defaultRootPath + real, options),
		client.getDirectoryContents(defaultRootPath + real, options),
	])
	const folder = resultToNode(self.data)
	folder.displayname = path.split('/').pop() // the lens' name (Familie), not the real one (04_Finanz)
	turned.set(folder.source, path)
	if (answer.fallback) {
		// The department folder is not born in this project: its own folder is shown. Saving
		// here would land in the project, not where it belongs: only through the embryo above.
		folder.permissions = Permission.READ
	}
	if (answer.unborn) {
		unborn.set(folder.source, { path, department: answer.unborn.slice(answer.real.length + 1), project: answer.real.split('/').pop() })
	} else {
		unborn.delete(folder.source)
	}
	const contents = entries.data.map(entry => resultToNode(entry))
	for (const node of contents) {
		if (node.type === FileType.Folder) {
			turned.set(node.source, join(path, node.basename))
		}
	}
	return { folder, contents }
}

async function getContents(path) {
	path = '/' + (path ?? '/').split('/').filter(Boolean).join('/')
	const { status, data } = await askCore('lens', path)
	if (status !== 200 || !data) {
		return { folder: virtualFolder(path), contents: [] } // nothing here one may see
	}
	if (data.real !== null) {
		return realContents(path, data)
	}
	const contents = await Promise.all(data.entries.map(entry => entry.real
		? projectOnShelf(join(path, entry.name), data.place.replace(/\/$/, '') + entry.real)
		: virtualFolder(join(path, entry.name))))
	return { folder: virtualFolder(path), contents }
}

/**
 * A project on the shelf as its real department folder (Familie = Familie/04_Finanz): the
 * details, downloading and sharing act on that folder. Named after the project, and only to
 * read here - renaming "Familie" must not rename Familie/04_Finanz.
 */
async function projectOnShelf(path, real) {
	try {
		const result = await getClient().stat(defaultRootPath + real, { details: true, data: getDefaultPropfind() })
		const node = resultToNode(result.data)
		node.displayname = path.split('/').pop()
		node.permissions = Permission.READ
		turned.set(node.source, path)
		return node
	} catch (error) {
		console.error('MyOS', error)
		return virtualFolder(path)
	}
}

function open(path) {
	window.OCP.Files.Router.goToRoute(null, { view: VIEW }, { dir: path })
}

/**
 * Bears the department folder the lens at path shows as an embryo, then puts files in it;
 * folder is the one shown there (the project's), which the Files app then fetches anew.
 */
async function bearHere(path, folder, files) {
	const { status, data } = await askCore('bear', path)
	if (status !== 200 || !data) {
		throw new Error(`bear ${path}: ${status}`)
	}
	await carryOut(data)
	for (const file of files) {
		await upload(data.real, file)
	}
	// The core sees the change a few seconds later (it rebuilds its shadow): wait for it, then
	// the Files app asks this view again - now the lens shows the born folder.
	for (let tries = 0; tries < 30; tries++) {
		const { data } = await askCore('lens', path)
		if (data && !data.fallback) {
			break
		}
		await new Promise(resolve => setTimeout(resolve, 1000))
	}
	emit('files:node:updated', folder)
}

function renderUnborn(folder) {
	const el = header.el
	if (!el) {
		return
	}
	el.replaceChildren()
	const here = unborn.get(folder?.source)
	if (!here) {
		return
	}
	const label = document.createElement('span')
	label.className = 'myos-row__label'
	label.textContent = t(APP, 'Not in {project} yet:', { project: here.project })
	const button = document.createElement('button')
	button.type = 'button'
	button.className = 'myos-folder myos-folder--embryo'
	button.title = t(APP, 'Click to create it here, or drop files on it')
	button.innerHTML = folderIcon
	button.append(document.createTextNode(here.department))
	const failed = error => console.error('MyOS', error)
	button.addEventListener('click', () => bearHere(here.path, folder, []).catch(failed))
	button.addEventListener('dragover', event => {
		event.preventDefault()
		button.classList.add('myos-folder--drop')
	})
	button.addEventListener('dragleave', () => button.classList.remove('myos-folder--drop'))
	button.addEventListener('drop', event => {
		event.preventDefault()
		event.stopPropagation() // not also into the folder shown below
		bearHere(here.path, folder, [...event.dataTransfer.files]).catch(failed)
	})
	el.append(label, button)
}

export function registerPerspectives() {
	// The action at once (the Files app reads its actions early); it acts only in this view.
	registerFileAction(new FileAction({
		id: 'myos-open-in-lens',
		displayName: () => t(APP, 'Open'),
		iconSvgInline: () => glassesIcon,
		enabled: (nodes, view) => view.id === VIEW && nodes.length === 1 && turned.has(nodes[0].source),
		exec: async node => {
			open(turned.get(node.source))
			return null
		},
		default: DefaultType.HIDDEN,
		order: -101, // before the Files app's own "open-folder" (-100), which opens the real path
	}))
	registerFileListHeaders(new Header({
		id: 'myos-lens-unborn',
		order: 0,
		enabled: (folder, view) => view.id === VIEW,
		render(el, folder) {
			header.el = document.createElement('div')
			header.el.className = 'myos-row'
			el.append(header.el)
			renderUnborn(folder)
		},
		updated(folder) {
			renderUnborn(folder)
		},
	}))
	// The view at once too, so a page opened in it (reloaded, a link) finds it; it goes again
	// for who is none of the people of a project the core knows.
	getNavigation().register(new View({
		id: VIEW,
		name: t(APP, 'Perspectives'),
		caption: t(APP, 'The projects seen from a department'),
		emptyTitle: t(APP, 'Nothing here'),
		emptyCaption: t(APP, 'This folder is empty, or holds nothing you may see'),
		icon: glassesIcon,
		order: 30,
		getContents,
	}))
	askCore('lens', '/').then(({ status }) => {
		if (status !== 200) {
			getNavigation().remove(VIEW)
		}
	}).catch(error => console.error('MyOS', error))
}
