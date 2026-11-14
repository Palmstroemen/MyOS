<?php

declare(strict_types=1);

namespace OCA\Seiton\AppInfo;

use OCA\Files\Event\LoadAdditionalScriptsEvent;
use OCA\Seiton\Listener\ForwardChanges;
use OCA\Seiton\Listener\LoadFilesScripts;
use OCA\Seiton\Listener\LockNewEntries;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Files\Events\Node\NodeCopiedEvent;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\Events\Node\NodeDeletedEvent;
use OCP\Files\Events\Node\NodeRenamedEvent;
use OCP\Files\Events\Node\NodeWrittenEvent;

class Application extends App implements IBootstrap {
	public const APP_ID = 'seiton';

	public function __construct() {
		parent::__construct(self::APP_ID);
	}

	public function register(IRegistrationContext $context): void {
		// Every way an entry comes into a folder: created, moved or renamed, copied.
		$context->registerEventListener(NodeCreatedEvent::class, LockNewEntries::class);
		$context->registerEventListener(NodeRenamedEvent::class, LockNewEntries::class);
		$context->registerEventListener(NodeCopiedEvent::class, LockNewEntries::class);
		// Every change in a Team folder goes to the Seiton core, which brings the rules in step.
		foreach ([NodeCreatedEvent::class, NodeRenamedEvent::class, NodeCopiedEvent::class,
			NodeDeletedEvent::class, NodeWrittenEvent::class] as $event) {
			$context->registerEventListener($event, ForwardChanges::class);
		}
		// The row of Seiton folders above the file list.
		$context->registerEventListener(LoadAdditionalScriptsEvent::class, LoadFilesScripts::class);
	}

	public function boot(IBootContext $context): void {
	}
}
