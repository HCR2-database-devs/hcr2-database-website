<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('delete_record connection failed: ' . $e->getMessage());
}

$data = json_decode(file_get_contents('php://input'), true);

$recordKey = parse_record_key($data['recordId'] ?? null);
if (!$recordKey) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid recordId']);
    exit;
}

try {
    $db->beginTransaction();
    $stmt = $db->prepare('DELETE FROM _worldrecord WHERE ' . record_key_where_sql() . ' AND current = 1');
    $stmt->execute(record_key_params($recordKey));
    $dryRun = finish_dry_run_transaction($db);

    echo json_encode(['success' => true, 'dryRun' => $dryRun, 'deleted' => $stmt->rowCount()]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('delete_record failed: ' . $e->getMessage());
}
?>
