<?php

declare(strict_types=1);

namespace OCA\MyOSAcl\AppInfo;

use OCA\MyOSAcl\Listener\LockNewEntries;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Files\Events\Node\NodeCopiedEvent;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\Events\Node\NodeRenamedEvent;

class Application extends App implements IBootstrap {
	public const APP_ID = 'myos_acl';

	public function __construct() {
		parent::__construct(self::APP_ID);
	}

	public function register(IRegistrationContext $context): void {
		// Every way an entry comes into a folder: created, moved or renamed, copied.
		$context->registerEventListener(NodeCreatedEvent::class, LockNewEntries::class);
		$context->registerEventListener(NodeRenamedEvent::class, LockNewEntries::class);
		$context->registerEventListener(NodeCopiedEvent::class, LockNewEntries::class);
	}

	public function boot(IBootContext $context): void {
	}
}
