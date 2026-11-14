<?php

declare(strict_types=1);

namespace OCA\Seiton\Listener;

use OCA\GroupFolders\Mount\GroupMountPoint;
use OCA\Seiton\AppInfo\Application;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\AbstractNodeEvent;
use OCP\Files\Events\Node\AbstractNodesEvent;
use OCP\Files\FileInfo;
use OCP\Files\Node;
use OCP\Http\Client\IClientService;
use OCP\IAppConfig;
use Psr\Log\LoggerInterface;

/**
 * Tells the Seiton core service (cloud/service/server.py, POST /changed) what changed in a Team
 * folder: created, renamed, copied, deleted, written - the path in the Team folder and whether
 * it is a folder. No Seiton logic here: the core decides what matters (its shadow tree holds
 * folders and .seiton files) and brings the rules in step at once, instead of at its next look
 * at the Team folder's ETag ("Designdocument Seiton Core Service.md", 4).
 *
 * @template-implements IEventListener<Event>
 */
class ForwardChanges implements IEventListener {
	public function __construct(
		private readonly IClientService $clients,
		private readonly IAppConfig $config,
		private readonly LoggerInterface $logger,
	) {
	}

	public function handle(Event $event): void {
		if ($event instanceof AbstractNodesEvent) { // renamed, copied: where it was and where it is
			$nodes = [$event->getSource(), $event->getTarget()];
		} elseif ($event instanceof AbstractNodeEvent) {
			$nodes = [$event->getNode()];
		} else {
			return;
		}
		$url = rtrim($this->config->getValueString(Application::APP_ID, 'core_url'), '/');
		$secret = $this->config->getValueString(Application::APP_ID, 'core_secret');
		if ($url === '' || $secret === '') {
			return;
		}
		$changes = [];
		$folder = null;
		foreach ($nodes as $node) {
			try {
				$change = $this->change($node);
			} catch (\Throwable $e) {
				continue; // e.g. a node already gone; the core's look at the ETag catches up
			}
			if ($change !== null) {
				[$folder, $changes[]] = $change;
			}
		}
		if ($changes === []) {
			return;
		}
		try {
			$this->clients->newClient()->post($url . '/changed', [
				'headers' => ['X-Seiton-Secret' => $secret, 'Content-Type' => 'application/json'],
				'body' => json_encode(['folder' => $folder, 'changes' => $changes]),
				'timeout' => 2, // never hold up the user's request for long
				'nextcloud' => ['allow_local_address' => true],
			]);
		} catch (\Throwable $e) {
			// The core catches up at its next look at the Team folder's ETag.
			$this->logger->warning('Seiton: could not tell the Seiton core about a change: ' . $e->getMessage());
		}
	}

	/** [Team folder name, ['path' => in the Team folder, 'dir' => bool]], null outside Team folders. */
	private function change(Node $node): ?array {
		$mount = $node->getMountPoint();
		if (!$mount instanceof GroupMountPoint) {
			return null;
		}
		$folder = basename(rtrim($mount->getMountPoint(), '/'));
		$path = '/' . ltrim($node->getInternalPath(), '/');
		return [$folder, ['path' => $path, 'dir' => $node->getType() === FileInfo::TYPE_FOLDER]];
	}
}
