/**
 * Asking the MyOS core (cloud/service/server.py) through myos_acl's CoreController: the core
 * decides, the browser shows its answer and acts with the user's own rights.
 */
import { getRequestToken } from '@nextcloud/auth'
import { generateOcsUrl } from '@nextcloud/router'

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
