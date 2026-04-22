<?php
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../auth/check_auth.php';
$user = ensure_authorized_json();

try {
    $input = json_decode(file_get_contents('php://input'), true);
    if (!$input) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON']);
        exit;
    }

    $recordKey = parse_record_key($input['recordId'] ?? null);
    $questionable = $input['questionable'] ?? null;
    $note = $input['note'] ?? $input['reason'] ?? null;

    if (!$recordKey) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid recordId']);
        exit;
    }

    if ($questionable === null || ($questionable !== 0 && $questionable !== 1)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid questionable value (must be 0 or 1)']);
        exit;
    }

    try {
        $pdo = get_database_connection();
        $checkStmt = $pdo->prepare('SELECT 1 FROM _worldrecord WHERE ' . record_key_where_sql() . ' AND current = 1 LIMIT 1');
        $checkStmt->execute(record_key_params($recordKey));
        if (!$checkStmt->fetch()) {
            http_response_code(404);
            echo json_encode(['error' => 'Record not found']);
            exit;
        }

        $pdo->beginTransaction();
        $updateStmt = $pdo->prepare('UPDATE _worldrecord SET questionable = :questionable, questionable_reason = :note WHERE ' . record_key_where_sql() . ' AND current = 1');
        $updateStmt->execute(array_merge([
            ':questionable' => $questionable,
            ':note' => $note,
        ], record_key_params($recordKey)));
        $dryRun = finish_dry_run_transaction($pdo);

        http_response_code(200);
        echo json_encode([
            'success' => true,
            'dryRun' => $dryRun,
            'message' => 'Record status updated successfully'
        ]);

    } catch (PDOException $e) {
        if (isset($pdo) && $pdo->inTransaction()) {
            $pdo->rollBack();
        }
        generic_database_error('set_questionable failed: ' . $e->getMessage());
    }

} catch (PDOException $e) {
    generic_database_error('set_questionable parse failed: ' . $e->getMessage());
}
?>
