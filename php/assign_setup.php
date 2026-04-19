<?php
require_once __DIR__ . '/../auth/config.php';
if (session_status() === PHP_SESSION_NONE) session_start();

$logged = isset($_SESSION['discord']) && isset($_SESSION['discord']['id']);
$allowed = false;
if ($logged && !empty($ALLOWED_DISCORD_IDS)) {
    $allowed = in_array((string)$_SESSION['discord']['id'], $ALLOWED_DISCORD_IDS, true);
}
if (!$logged || !$allowed) {
    http_response_code(403);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

header('Content-Type: application/json');

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
if (!$input || !isset($input['recordId']) || !isset($input['tuningSetupId'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required parameters']);
    exit;
}

$recordId = (int)$input['recordId'];
$tuningSetupId = (int)$input['tuningSetupId'];

try {
    $stmt = $db->prepare("SELECT idTuningSetup FROM WorldRecord WHERE idRecord = ?");
    $stmt->execute([$recordId]);
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
    
    $stmt = $db->prepare("SELECT idTuningSetup FROM TuningSetup WHERE idTuningSetup = ?");
    $stmt->execute([$tuningSetupId]);
    if (!$stmt->fetch()) {
        http_response_code(404);
        echo json_encode(['error' => 'Tuning setup not found']);
        exit;
    }
    
    $stmt = $db->prepare("UPDATE WorldRecord SET idTuningSetup = ? WHERE idRecord = ?");
    $stmt->execute([$tuningSetupId, $recordId]);
    
    echo json_encode(['success' => true]);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>