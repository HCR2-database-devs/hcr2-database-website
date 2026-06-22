<?php
if (!function_exists('safe_json_error')) {
    function safe_json_error(string $message, int $statusCode = 500): void {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
            http_response_code($statusCode);
        }
        echo json_encode(['error' => $message]);
        exit;
    }
}

try {
    require_once __DIR__ . '/../auth/config.php';
} catch (Throwable $e) {
    safe_json_error('Server configuration error');
}

require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();

header('Content-Type: application/json; charset=utf-8');

if (!defined('HCAPTCHA_SITE_KEY') || empty(HCAPTCHA_SITE_KEY)) {
    safe_json_error('hCaptcha is not configured');
}

echo json_encode(['sitekey' => HCAPTCHA_SITE_KEY]);
?>
