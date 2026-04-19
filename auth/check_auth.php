<?php
require_once __DIR__ . '/config.php';

function base64url_decode($data) {
    return json_decode(base64_decode(strtr($data, '-_', '+/')), true);
}

function verify_token($jwt, $secret) {
    $parts = explode('.', $jwt);
    if (count($parts) !== 3) return false;

    [$h, $p, $s] = $parts;
    $data = "$h.$p";

    $sig = rtrim($s, '=');

    $calc = rtrim(strtr(
        base64_encode(hash_hmac('sha256', $data, $secret, true)),
        '+/', '-_'
    ), '=');

    if (!hash_equals($calc, $sig)) return false;

    $payload = base64url_decode($p);
    if (!$payload || ($payload['exp'] ?? 0) < time() - 30) return false;

    return $payload;
}


function ensure_authorized() {
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }

    if (empty($_COOKIE['WC_TOKEN'])) {
        header('Location: /');
        exit;
    }

    $payload = verify_token($_COOKIE['WC_TOKEN'], AUTH_SHARED_SECRET);
    if (!$payload) {
        setcookie('WC_TOKEN', '', [
            'expires' => time() - 3600,
            'path' => '/',
            'domain' => '.hcr2.xyz',
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Lax'
        ]);
        header('Location: /');
        exit;
    }

    $_SESSION['discord'] = [
        'id' => $payload['sub'],
        'username' => $payload['username']
    ];

    return $payload;
}

function ensure_authorized_json() {
    session_start();

    if (empty($_COOKIE['WC_TOKEN'])) {
        http_response_code(401);
        echo json_encode(['logged' => false]);
        exit;
    }

    $payload = verify_token($_COOKIE['WC_TOKEN'], AUTH_SHARED_SECRET);
    if (!$payload) {
        setcookie('WC_TOKEN', '', [
            'expires' => time() - 3600,
            'path' => '/',
            'domain' => '.hcr2.xyz',
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Lax'
        ]);
        http_response_code(401);
        echo json_encode(['logged' => false]);
        exit;
    }

    $_SESSION['discord'] = [
        'id' => $payload['sub'],
        'username' => $payload['username']
    ];

    global $ALLOWED_DISCORD_IDS;
    if (!empty($ALLOWED_DISCORD_IDS) && !in_array($payload['sub'], $ALLOWED_DISCORD_IDS, true)) {
        http_response_code(403);
        echo json_encode(['logged' => false]);
        exit;
    }

    return $payload;
}