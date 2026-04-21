<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/check_auth.php';

if (session_status() === PHP_SESSION_NONE) {
    session_set_cookie_params([
        'domain' => '.hcr2.xyz',
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}

header('Content-Type: application/json');

if (empty($_COOKIE['WC_TOKEN'])) {
    error_log('[AUTH] WC_TOKEN cookie is missing or empty');
    echo json_encode([
        'logged' => false,
        'allowed' => false
    ]);
    exit;
}
$payload = verify_token($_COOKIE['WC_TOKEN'], AUTH_SHARED_SECRET);

if (!$payload) {
    error_log('[AUTH] Token verification failed');
    echo json_encode([
        'logged' => false,
        'allowed' => false
    ]);
    exit;
}
error_log('[AUTH] Token verified for user: ' . ($payload['username'] ?? $payload['sub']));
$_SESSION['discord'] = [
    'id' => $payload['sub'],
    'username' => $payload['username']
];

global $ALLOWED_DISCORD_IDS;
$allowed = in_array($payload['sub'], $ALLOWED_DISCORD_IDS, true);

echo json_encode([
    'logged' => true,
    'allowed' => $allowed,
    'id' => $payload['sub'],
    'username' => $payload['username']
]);
