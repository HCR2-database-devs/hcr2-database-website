<?php
ini_set('session.cookie_domain', '.hcr2.xyz'); 
ini_set('session.cookie_path', '/'); 
ini_set('session.cookie_secure', 1); 
ini_set('session.cookie_httponly', 1); 
ini_set('session.cookie_samesite', 'Lax'); 
session_start();

require_once __DIR__ . '/check_auth.php';
require_once __DIR__ . '/config.php';

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