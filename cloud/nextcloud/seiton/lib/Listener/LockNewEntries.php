<?php

declare(strict_types=1);

namespace OCA\Seiton\Listener;

use OCA\GroupFolders\ACL\Rule;
use OCA\GroupFolders\ACL\RuleManager;
use OCA\GroupFolders\Mount\GroupMountPoint;
use OCP\Constants;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCopiedEvent;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\Events\Node\NodeRenamedEvent;
use OCP\Files\Node;
use Psr\Log\LoggerInterface;

/**
 * An entry that comes into a Team folder's folder gets, for everyone whose rule on that
 * folder is a rule on the way (core/acl_nextcloud.py: it fixes every permission but share,
 * mask 15), a rule of its own: the same permissions without read, every bit fixed. So it
 * does not inherit the read that was given only to pass. Rules the entry already has (it
 * was moved in with them) stay.
 *
 * @template-implements IEventListener<Event>
 */
class LockNewEntries implements IEventListener {
	private const FULL_MASK = 31;
	private const TRAVERSE_MASK = self::FULL_MASK & ~Constants::PERMISSION_SHARE;

	public function __construct(
		private readonly RuleManager $ruleManager,
		private readonly LoggerInterface $logger,
	) {
	}

	public function handle(Event $event): void {
		if ($event instanceof NodeCreatedEvent) {
			$node = $event->getNode();
		} elseif ($event instanceof NodeRenamedEvent || $event instanceof NodeCopiedEvent) {
			$node = $event->getTarget();
		} else {
			return;
		}
		try {
			$this->lock($node);
		} catch (\Throwable $e) {
			// Security: the entry stays readable on the way until the next myacl sync.
			$this->logger->error('Seiton: could not lock ' . $node->getPath() . ': ' . $e->getMessage(), ['exception' => $e]);
		}
	}

	private function lock(Node $node): void {
		$mount = $node->getMountPoint();
		if (!$mount instanceof GroupMountPoint) {
			return;
		}
		$internal = $node->getInternalPath();
		if ($internal === '') {
			return; // the Team folder itself
		}
		$parent = dirname($internal);
		// Paths as the Team folders app keys its rules (DAV/ACLPlugin.php).
		$source = $mount->getSourcePath();
		$parentPath = trim($source . '/' . ($parent === '.' ? '' : $parent), '/');
		$ownPath = trim($source . '/' . $internal, '/');
		$rules = $this->ruleManager->getAllRulesForPaths($mount->getNumericStorageId(), [$parentPath, $ownPath]);

		$own = [];
		foreach ($rules[$ownPath] ?? [] as $rule) {
			$own[$rule->getUserMapping()->getKey()] = true;
		}
		$locked = false;
		foreach ($rules[$parentPath] ?? [] as $rule) {
			$mapping = $rule->getUserMapping();
			if ($rule->getMask() !== self::TRAVERSE_MASK || isset($own[$mapping->getKey()])) {
				continue;
			}
			$permissions = $rule->getPermissions() & ~Constants::PERMISSION_READ;
			$this->ruleManager->saveRule(new Rule($mapping, $node->getId(), self::FULL_MASK, $permissions));
			$locked = true;
		}
		if ($locked) {
			$node->getStorage()->getPropagator()->propagateChange($internal, time());
		}
	}
}
