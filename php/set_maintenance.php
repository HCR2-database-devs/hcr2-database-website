<?php
require_once __DIR__ . '/../auth/check_auth.php';
require_once __DIR__ . '/maintenance_helpers.php';
header('Content-Type: application/json; charset=utf-8');

ensure_authorized_json();

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
$action = $data['action'] ?? $_POST['action'] ?? null;

$path = maintenance_flag_path();
try {
    if (api_dry_run_enabled()) {
        $next = $action === 'enable' || $action === 'on' || $action === '1'
            ? true
            : (($action === 'disable' || $action === 'off' || $action === '0') ? false : !file_exists($path));
        echo json_encode(['success' => true, 'dryRun' => true, 'maintenance' => $next]);
        exit;
    }

    if ($action === 'enable' || $action === 'on' || $action === '1') {
        file_put_contents($path, "1");
        echo json_encode(['success' => true, 'maintenance' => true]);
        exit;
    }
    if ($action === 'disable' || $action === 'off' || $action === '0') {
        if (file_exists($path)) unlink($path);
        echo json_encode(['success' => true, 'maintenance' => false]);
        exit;
    }
    if (file_exists($path)) { unlink($path); $m=false; } else { file_put_contents($path, "1"); $m=true; }
    echo json_encode(['success' => true, 'maintenance' => $m]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to change maintenance state']);
}

?>
