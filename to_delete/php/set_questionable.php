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

    $recordId = $input['recordId'] ?? null;
    $questionable = $input['questionable'] ?? null;
    $note = $input['note'] ?? $input['reason'] ?? null;

    if (!$recordId) {
        http_response_code(400);
        echo json_encode(['error' => 'Missing recordId']);
        exit;
    }

    if ($questionable === null || ($questionable !== 0 && $questionable !== 1)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid questionable value (must be 0 or 1)']);
        exit;
    }

    try {
        $pdo = get_database_connection();
        $checkStmt = $pdo->prepare('SELECT idRecord FROM _worldrecord WHERE idRecord = ?');
        $checkStmt->execute([$recordId]);
        if (!$checkStmt->fetch()) {
            http_response_code(404);
            echo json_encode(['error' => 'Record not found']);
            exit;
        }

        $updateStmt = $pdo->prepare('UPDATE _worldrecord SET questionable = ?, questionable_reason = ? WHERE idRecord = ?');
        $updateStmt->execute([$questionable, $note, $recordId]);

        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Record status updated successfully'
        ]);

    } catch (PDOException $e) {
        generic_database_error('set_questionable failed: ' . $e->getMessage());
    }

} catch (PDOException $e) {
    generic_database_error('set_questionable parse failed: ' . $e->getMessage());
}
?>