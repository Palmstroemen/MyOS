<?php

declare(strict_types=1);

namespace OCA\MyOSAcl\Controller;

use OCA\MyOSAcl\AppInfo\Application;
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
 * The bridge to the MyOS core service (cloud/service/server.py): what a turned path stands
 * for, as the core answers it for the logged-in account. No MyOS logic here - the core
 * decides, this only passes the account on ("Designdocument MyOS Core Service.md", 4 and 6).
 * Set by the admin: occ config:app:set myos_acl core_url --value=http://myos-core:8080
 * and occ config:app:set myos_acl core_secret --sensitive --value=...
 */
class LensController extends OCSController {
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
	public function get(string $path = '/'): DataResponse {
		$user = $this->session->getUser();
		if ($user === null) {
			return new DataResponse(['error' => 'not logged in'], Http::STATUS_UNAUTHORIZED);
		}
		$url = rtrim($this->config->getValueString(Application::APP_ID, 'core_url'), '/');
		$secret = $this->config->getValueString(Application::APP_ID, 'core_secret');
		if ($url === '' || $secret === '') {
			return new DataResponse(['error' => 'the MyOS core is not set up'], Http::STATUS_SERVICE_UNAVAILABLE);
		}
		try {
			$response = $this->clients->newClient()->get($url . '/lens?' . http_build_query(['path' => $path]), [
				'headers' => ['X-MyOS-Secret' => $secret, 'X-MyOS-Account' => $user->getUID()],
				'http_errors' => false,
				'timeout' => 10,
				// The core runs next to Nextcloud, in its own network.
				'nextcloud' => ['allow_local_address' => true],
			]);
		} catch (\Throwable $e) {
			$this->logger->error('MyOS ACL: the MyOS core is not reachable: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'the MyOS core is not reachable'], Http::STATUS_BAD_GATEWAY);
		}
		$status = $response->getStatusCode();
		if ($status === Http::STATUS_UNAUTHORIZED) {
			// The core refused the bridge (wrong secret), not the user.
			$this->logger->error('MyOS ACL: the MyOS core refused the shared secret');
			return new DataResponse(['error' => 'the MyOS core refused the bridge'], Http::STATUS_BAD_GATEWAY);
		}
		$body = json_decode((string)$response->getBody(), true);
		return new DataResponse(is_array($body) ? $body : [], $status);
	}
}
