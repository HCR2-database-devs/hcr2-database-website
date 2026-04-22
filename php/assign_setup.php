<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

header('Content-Type: application/json');

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('assign_setup connection failed: ' . $e->getMessage());
}

$input = json_decode(file_get_contents('php://input'), true);
if (!$input || !isset($input['recordId']) || !isset($input['tuningSetupId'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required parameters']);
    exit;
}

$recordKey = parse_record_key($input['recordId']);
if (!$recordKey) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid recordId']);
    exit;
}
$tuningSetupId = (int)$input['tuningSetupId'];

try {
    $stmt = $db->prepare('SELECT "idTuningSetup" FROM _worldrecord WHERE ' . record_key_where_sql() . ' AND current = 1 LIMIT 1');
    $stmt->execute(record_key_params($recordKey));
    $record = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$record) {
        http_response_code(404);
        echo json_encode(['error' => 'Record not found']);
        exit;
    }
    
    if ($record['idTuningSetup']) {
        http_response_code(400);
        echo json_encode(['error' => 'Record already has a tuning setup assigned']);
        exit;
    }
    
    $stmt = $db->prepare('SELECT "idTuningSetup" FROM _tuningsetup WHERE "idTuningSetup" = ?');
    $stmt->execute([$tuningSetupId]);
    if (!$stmt->fetch()) {
        http_response_code(404);
        echo json_encode(['error' => 'Tuning setup not found']);
        exit;
    }
    
    $db->beginTransaction();
    $stmt = $db->prepare('UPDATE _worldrecord SET "idTuningSetup" = :setupId WHERE ' . record_key_where_sql() . ' AND current = 1');
    $stmt->execute(array_merge([
        ':setupId' => (string)$tuningSetupId,
    ], record_key_params($recordKey)));
    $dryRun = finish_dry_run_transaction($db);
    
    echo json_encode(['success' => true, 'dryRun' => $dryRun]);
    
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('assign_setup failed: ' . $e->getMessage());
}
?>
