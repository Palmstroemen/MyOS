<?php

declare(strict_types=1);

namespace OCA\Seiton\Controller;

use OCA\Seiton\AppInfo\Application;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\ApiRoute;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\Http\Client\IClientService;
use OCP\IAppConfig;
use OCP\IRequest;
use OCP\IUserSession;
use Psr\Log\LoggerInterface;

/**
 * The bridge to the Seiton core service (cloud/service/server.py): what a turned path stands
 * for (lens), the Seiton folders of a level (level), what a birth does (birth), what saving
 * through a lens needs first (bear) and the tags a folder's project suggests (tags), as the core
 * answers them for the logged-in account. No Seiton logic here - the core decides, this only
 * passes the account on ("Designdocument Seiton Core Service.md", 4 and 6).
 * Set by the admin: occ config:app:set seiton core_url --value=http://seiton-core:8080
 * and occ config:app:set seiton core_secret --sensitive --value=...
 */
class CoreController extends OCSController {
	public function __construct(
		string $appName,
		IRequest $request,
		private readonly IClientService $clients,
		private readonly IAppConfig $config,
		private readonly IUserSession $session,
		private readonly LoggerInterface $logger,
	) {
		parent::__construct($appName, $request);
	}

	#[NoAdminRequired]
	#[ApiRoute(verb: 'GET', url: '/api/v1/lens')]
	public function lens(string $path = '/'): DataResponse {
		return $this->ask('lens', $path);
	}

	#[NoAdminRequired]
	#[ApiRoute(verb: 'GET', url: '/api/v1/level')]
	public function level(string $path = '/'): DataResponse {
		return $this->ask('level', $path);
	}

	#[NoAdminRequired]
	#[ApiRoute(verb: 'GET', url: '/api/v1/birth')]
	public function birth(string $path = '/'): DataResponse {
		return $this->ask('birth', $path);
	}

	#[NoAdminRequired]
	#[ApiRoute(verb: 'GET', url: '/api/v1/bear')]
	public function bear(string $path = '/'): DataResponse {
		return $this->ask('bear', $path);
	}

	#[NoAdminRequired]
	#[ApiRoute(verb: 'GET', url: '/api/v1/tags')]
	public function tags(string $path = '/'): DataResponse {
		return $this->ask('tags', $path);
	}

	private function ask(string $question, string $path): DataResponse {
		$user = $this->session->getUser();
		if ($user === null) {
			return new DataResponse(['error' => 'not logged in'], Http::STATUS_UNAUTHORIZED);
		}
		$url = rtrim($this->config->getValueString(Application::APP_ID, 'core_url'), '/');
		$secret = $this->config->getValueString(Application::APP_ID, 'core_secret');
		if ($url === '' || $secret === '') {
			return new DataResponse(['error' => 'the Seiton core is not set up'], Http::STATUS_SERVICE_UNAVAILABLE);
		}
		try {
			$response = $this->clients->newClient()->get($url . '/' . $question . '?' . http_build_query(['path' => $path]), [
				'headers' => ['X-Seiton-Secret' => $secret, 'X-Seiton-Account' => $user->getUID()],
				'http_errors' => false,
				'timeout' => 10,
				// The core runs next to Nextcloud, in its own network.
				'nextcloud' => ['allow_local_address' => true],
			]);
		} catch (\Throwable $e) {
			$this->logger->error('Seiton: the Seiton core is not reachable: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'the Seiton core is not reachable'], Http::STATUS_BAD_GATEWAY);
		}
		$status = $response->getStatusCode();
		if ($status === Http::STATUS_UNAUTHORIZED) {
			// The core refused the bridge (wrong secret), not the user.
			$this->logger->error('Seiton: the Seiton core refused the shared secret');
			return new DataResponse(['error' => 'the Seiton core refused the bridge'], Http::STATUS_BAD_GATEWAY);
		}
		$body = json_decode((string)$response->getBody(), true);
		return new DataResponse(is_array($body) ? $body : [], $status);
	}
}
