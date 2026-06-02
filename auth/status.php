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
    echo json_encode([
        'logged' => false,
        'allowed' => false
    ]);
    exit;
}
$payload = verify_token($_COOKIE['WC_TOKEN'], AUTH_SHARED_SECRET);

if (!$payload) {
    echo json_encode([
        'logged' => false,
        'allowed' => false
    ]);
    exit;
}
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
