<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();

$backups_dir = __DIR__ . '/../backups';

if (!file_exists($backups_dir)) @mkdir($backups_dir, 0750, true);

if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['action']) && $_GET['action'] === 'download_db') {
    http_response_code(501);
    echo "PostgreSQL database download via this endpoint is not supported.";
    exit;
}

header('Content-Type: application/json; charset=utf-8');

$action = $_POST['action'] ?? null;

try {
    if ($action === 'create_backup') {
        throw new Exception('PostgreSQL backup creation is not supported by this endpoint.');
    }

    if ($action === 'list_backups') {
        $files = array_values(array_filter(scandir($backups_dir), function($f){ return $f !== '.' && $f !== '..'; }));
        $list = [];
        foreach ($files as $f) {
            $path = $backups_dir . '/' . $f;
            if (!is_file($path)) continue;
            $list[] = [
                'name' => $f,
                'size' => filesize($path),
                'mtime' => date('Y-m-d H:i:s', filemtime($path))
            ];
        }
        echo json_encode(['backups' => $list]);
        exit;
    }

    if ($action === 'delete') {
        $filename = $_POST['filename'] ?? '';
        $path = realpath($backups_dir . '/' . basename($filename));
        if (!$path || strpos($path, realpath($backups_dir)) !== 0) throw new Exception('Invalid filename');
        if (!file_exists($path)) throw new Exception('File not found');
        unlink($path);
        echo json_encode(['success' => true]);
        exit;
    }

    if ($action === 'restore') {
        throw new Exception('PostgreSQL restore is not supported by this endpoint.');
    }

    if ($action === 'import') {
        throw new Exception('PostgreSQL SQL import is not supported by this endpoint.');
    }

    if ($action === 'integrity') {
        $db = get_database_connection();
        $stmt = $db->query('SELECT 1');
        $result = $stmt->fetchColumn();
        echo json_encode(['ok' => true, 'result' => $result]);
        exit;
    }

    echo json_encode(['error' => 'Unknown action']);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
