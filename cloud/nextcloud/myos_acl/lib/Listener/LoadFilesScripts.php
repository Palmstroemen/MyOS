<?php

declare(strict_types=1);

namespace OCA\MyOSAcl\Listener;

use OCA\Files\Event\LoadAdditionalScriptsEvent;
use OCA\MyOSAcl\AppInfo\Application;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Util;

/**
 * The Files app gets the row of MyOS folders and the view "Perspectives" (src/main.js, built
 * to js/myos_acl-main.js). As an init script, loaded before the Files app: a page opened in
 * the view (reloaded, a link) finds it registered.
 *
 * @template-implements IEventListener<LoadAdditionalScriptsEvent>
 */
class LoadFilesScripts implements IEventListener {
	public function handle(Event $event): void {
		if (!$event instanceof LoadAdditionalScriptsEvent) {
			return;
		}
		Util::addInitScript(Application::APP_ID, 'myos_acl-main');
	}
}
