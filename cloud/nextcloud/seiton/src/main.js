/**
 * Seiton folders in the Files app: above the file list one row with the Seiton folders of the
 * current folder, always together - born ones in full colour, embryos (suggested, not yet
 * created) pale. The born ones leave the list below, so it holds what the user made.
 *
 * Which folders a level holds, and what a birth creates and copies, the Seiton core answers
 * (cloud/service/level.py, through seiton's CoreController): born ones the user may read,
 * embryos where the user may create, as Scope with ACLs enforced. The browser shows that and
 * gives birth with the user's own rights - Nextcloud checks them once more.
 *
 * Next to them the tags the project suggests (its Tags.md, through the core; in the cloud they
 * are Nextcloud's collaborative tags): a click shows only what carries that tag here, as
 * Scope's tag bar does.
 */
import { FileListFilter, Header, getNavigation, registerFileListFilter, registerFileListHeaders } from '@nextcloud/files'
import { t } from '@nextcloud/l10n'
import { askCore, carryOut, folderIcon } from './core.js'
import { registerPerspectives } from './lens.js'

const APP = 'seiton'
const EMBRYO_OPACITY = 0.4 // as Scope's default for suggested folders

// The folder shown and the core's answers for it: folders [{name, born}] and tags [names],
// null outside Seiton; tag: the one chosen to filter by.
const state = { folder: null, folders: null, tags: null, tag: null, el: null }

const style = `
.seiton-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 6px 12px; }
.seiton-row:empty { display: none; }
.seiton-row__label { color: var(--color-text-maxcontrast); font-size: 0.85em; margin-inline-end: 6px; }
.seiton-folder { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
	border: 1px solid var(--color-border); border-radius: var(--border-radius-pill, 16px);
	background: var(--color-main-background); color: var(--color-main-text); cursor: pointer; }
.seiton-folder:hover { background: var(--color-background-hover); }
.seiton-folder--embryo { opacity: ${EMBRYO_OPACITY}; border-style: dashed; }
.seiton-folder--embryo:hover { opacity: 0.7; }
.seiton-folder svg { width: 18px; height: 18px; fill: var(--color-primary-element); }
.seiton-folder--drop { opacity: 1; background: var(--color-primary-element-light); }
.seiton-row__label--tags { margin-inline-start: 12px; }
.seiton-tag { padding: 2px 10px; border: 1px solid var(--color-border); border-radius: var(--border-radius-pill, 16px);
	background: var(--color-main-background); color: var(--color-main-text); cursor: pointer; }
.seiton-tag:hover { background: var(--color-background-hover); }
.seiton-tag--chosen { background: var(--color-primary-element); color: var(--color-primary-element-text); }
`

function childPath(name) {
	return state.folder.path.replace(/\/$/, '') + '/' + name
}

function open(name) {
	window.OCP.Files.Router.goToRoute(null, { view: 'files' }, { dir: childPath(name) })
}

/** Birth as the core says (as Seiton' BirthClinic does): the folders, then the copies. */
async function birth(name) {
	const { status, data } = await askCore('birth', childPath(name))
	if (status !== 200 || !data) {
		throw new Error(`birth ${name}: ${status}`)
	}
	await carryOut(data)
	open(name)
}

function render() {
	const el = state.el
	if (!el) {
		return
	}
	el.replaceChildren()
	const folders = state.folders ?? []
	if (folders.length > 0) {
		const label = document.createElement('span')
		label.className = 'seiton-row__label'
		label.textContent = t(APP, 'Seiton folders')
		el.append(label)
	}
	for (const { name, born } of folders) {
		const button = document.createElement('button')
		button.type = 'button'
		button.className = 'seiton-folder' + (born ? '' : ' seiton-folder--embryo')
		button.title = born ? name : t(APP, 'Suggested folder: click to create it')
		button.innerHTML = folderIcon
		button.append(document.createTextNode(name))
		button.addEventListener('click', () => (born ? open(name) : birth(name)).catch(error => console.error('Seiton', error)))
		el.append(button)
	}
	const tags = state.tags ?? []
	if (tags.length > 0) {
		const label = document.createElement('span')
		label.className = 'seiton-row__label seiton-row__label--tags'
		label.textContent = t(APP, 'Tags')
		el.append(label)
	}
	for (const tag of tags) {
		const button = document.createElement('button')
		button.type = 'button'
		button.className = 'seiton-tag' + (tag === state.tag ? ' seiton-tag--chosen' : '')
		button.title = t(APP, 'Show only what carries this tag')
		button.textContent = '#' + tag
		button.addEventListener('click', () => choose(tag === state.tag ? null : tag))
		el.append(button)
	}
}

/** Filters the list by tag (null: no more), as Scope's tag bar. */
function choose(tag) {
	state.tag = tag
	render()
	filter.changed()
}

async function show(folder) {
	if (state.folder?.source !== folder.source) {
		state.tag = null // a tag chosen there does not follow into another folder
	}
	state.folder = folder
	state.folders = null
	state.tags = null
	render()
	const [level, tags] = await Promise.all([askCore('level', folder.path), askCore('tags', folder.path)]
		.map(answer => answer.catch(() => ({ status: 0 }))))
	if (state.folder === folder) {
		state.folders = level.status === 200 ? level.data.folders : null
		state.tags = tags.status === 200 ? tags.data.tags : null
		render()
		filter.changed()
	}
}

/** The names of the collaborative tags a node carries, as the Files app lists them. */
function tagsOf(node) {
	const raw = node.attributes?.['system-tags']?.['system-tag']
	return [raw ?? []].flat().map(tag => String(typeof tag === 'object' ? tag?.text ?? '' : tag)).filter(Boolean)
}

class SeitonFolders extends FileListFilter {
	constructor() {
		super('seiton-folders', 0)
	}

	/** Takes the born Seiton folders out of the list (they are in the row); with a tag chosen,
	 * keeps only what carries it. */
	filter(nodes) {
		const folder = state.folder
		if (!folder || getNavigation().active?.id !== 'files') {
			return nodes // the row is only in "All files"
		}
		const born = new Set((state.folders ?? []).filter(f => f.born).map(f => f.name))
		return nodes.filter(node => node.dirname !== folder.path
			|| (!(node.type === 'folder' && born.has(node.basename)) && (!state.tag || tagsOf(node).includes(state.tag))))
	}

	changed() {
		this.updateChips(state.tag ? [{ text: '#' + state.tag, onclick: () => choose(null) }] : [])
		this.filterUpdated()
	}
}

const filter = new SeitonFolders()

const sheet = document.createElement('style')
sheet.textContent = style
document.head.append(sheet)

registerFileListFilter(filter)
registerFileListHeaders(new Header({
	id: 'seiton-folders',
	order: 0,
	enabled: (folder, view) => view.id === 'files',
	render(el, folder) {
		state.el = document.createElement('div')
		state.el.className = 'seiton-row'
		el.append(state.el)
		show(folder)
	},
	updated(folder) {
		show(folder)
	},
}))

registerPerspectives()
