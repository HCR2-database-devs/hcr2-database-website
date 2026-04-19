<?php
if (!empty($_GET['oauth_state']) || !empty($_GET['code'])) {
    header('Location: /');
    exit;
}

ini_set('session.cookie_domain', '.hcr2.xyz');
ini_set('session.cookie_path', '/');
ini_set('session.cookie_secure', 1);
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Lax');

session_start();

$_SESSION = array();
if (ini_get("session.use_cookies")) {
    $params = session_get_cookie_params();
    setcookie(session_name(), '', time() - 42000,
        $params["path"], $params["domain"],
        $params["secure"], $params["httponly"]
    );
}
session_destroy();

setcookie("WC_TOKEN", "", [
    'expires' => time() - 3600,
    'path' => '/',
    'domain' => '.hcr2.xyz',
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Lax'
]);

header("Location: /");
exit;