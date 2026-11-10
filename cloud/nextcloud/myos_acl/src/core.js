/**
 * What the row of MyOS folders and the view Perspectives share: asking the MyOS core
 * (cloud/service/server.py) through myos_acl's CoreController - the core decides, the browser
 * shows its answer - and acting over WebDAV with the user's own rights.
 */
import { getCurrentUser, getRequestToken } from '@nextcloud/auth'
import { generateOcsUrl, generateRemoteUrl } from '@nextcloud/router'

/** The core's answer to question ("lens", "level", "birth") for path: {status, data}. */
export async function askCore(question, path) {
	const url = generateOcsUrl('apps/myos_acl/api/v1/' + question) + '?format=json&path=' + encodeURIComponent(path)
	const response = await fetch(url, {
		headers: { 'OCS-APIRequest': 'true', Accept: 'application/json', requesttoken: getRequestToken() ?? '' },
		credentials: 'same-origin',
	})
	const body = await response.json().catch(() => null)
	return { status: response.status, data: body?.ocs?.data ?? null }
}

/** The WebDAV URL of path in the user's files. */
export function davUrl(path) {
	const root = generateRemoteUrl('dav/files/' + encodeURIComponent(getCurrentUser().uid))
	return root.replace(/\/$/, '') + path.split('/').filter(Boolean).map(p => '/' + encodeURIComponent(p)).join('')
}

export function dav(method, url, headers = {}, body = undefined) {
	return fetch(url, { method, body, headers: { requesttoken: getRequestToken() ?? '', ...headers }, credentials: 'same-origin' })
}

async function must(response, what) {
	if (!response.ok && response.status !== 405) { // 405: the folder is there already
		throw new Error(`${what}: ${response.status}`)
	}
}

/** Does what the core planned for a birth (birth, bear): the folders, then the copies. */
export async function carryOut(plan) {
	for (const folder of plan.create) {
		await must(await dav('MKCOL', davUrl(folder)), `MKCOL ${folder}`)
	}
	for (const copy of plan.copy) {
		await must(await dav('COPY', davUrl(copy.from), { Destination: davUrl(copy.to), Overwrite: 'F' }), `COPY ${copy.to}`)
	}
}

/** Puts file (a File the user dropped) into the folder at path; an existing one is kept. */
export async function upload(path, file) {
	const response = await dav('PUT', davUrl(path + '/' + file.name), { 'If-None-Match': '*' }, file)
	if (!response.ok) {
		throw new Error(`PUT ${file.name}: ${response.status}`)
	}
}

export const folderIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>'
