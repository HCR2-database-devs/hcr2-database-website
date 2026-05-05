<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();
header('Content-Type: application/json; charset=utf-8');

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('delete_news connection failed: ' . $e->getMessage());
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

$id = isset($data['id']) ? (int)$data['id'] : 0;

if ($id <= 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid news ID.']);
    exit;
}

try {
    $db->beginTransaction();
    $stmt = $db->prepare('DELETE FROM news WHERE id = :id');
    $stmt->execute([':id' => $id]);

    $dryRun = finish_dry_run_transaction($db);
    echo json_encode(['success' => true, 'dryRun' => $dryRun]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('delete_news failed: ' . $e->getMessage());
}
