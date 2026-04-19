<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('add_tuning_setup connection failed: ' . $e->getMessage());
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST ?? [];
}

$partIds = $data['partIds'] ?? [];
if (!is_array($partIds) || count($partIds) < 3 || count($partIds) > 4) {
    echo json_encode(['error' => 'Must select 3 or 4 tuning parts.']);
    exit;
}

sort($partIds);

try {
    $db->beginTransaction();

    $inPlaceholders = str_repeat('?,', count($partIds) - 1) . '?';
    $stmt = $db->prepare("
        SELECT idTuningSetup
        FROM _tuningsetup
        WHERE idTuningSetup IN (
            SELECT idTuningSetup
            FROM _tuningsetupparts
            WHERE idTuningPart IN ($inPlaceholders)
            GROUP BY idTuningSetup
            HAVING COUNT(*) = ?
        )
        AND NOT EXISTS (
            SELECT 1
            FROM _tuningsetupparts tsp
            WHERE tsp.idTuningSetup = _tuningsetup.idTuningSetup
            AND tsp.idTuningPart NOT IN ($inPlaceholders)
        )
    ");
    $params = array_merge($partIds, [count($partIds)], $partIds);
    $stmt->execute($params);
    $existing = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($existing) {
        $db->rollBack();
        echo json_encode(['error' => 'A setup with these parts already exists.']);
        exit;
    }

    $stmt = $db->prepare("INSERT INTO _tuningsetup DEFAULT VALUES");
    $stmt->execute();
    $setupId = $db->lastInsertId();

    $stmt = $db->prepare("INSERT INTO _tuningsetupparts (idTuningSetup, idTuningPart) VALUES (?, ?)");
    foreach ($partIds as $partId) {
        $stmt->execute([$setupId, $partId]);
    }

    $db->commit();
    echo json_encode(['success' => true]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('add_tuning_setup failed: ' . $e->getMessage());
}
?>