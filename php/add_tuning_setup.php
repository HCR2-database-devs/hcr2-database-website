<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (Throwable $e) {
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
            SELECT id_tuning_setup
        FROM tuning_setup
        WHERE id_tuning_setup IN (
            SELECT id_tuning_setup
            FROM tuning_setup_part
            WHERE id_tuning_part IN ($inPlaceholders)
            GROUP BY id_tuning_setup
            HAVING COUNT(*) = ?
        )
        AND NOT EXISTS (
            SELECT 1
            FROM tuning_setup_part tsp
            WHERE tsp.id_tuning_setup = tuning_setup.id_tuning_setup
              AND tsp.id_tuning_part NOT IN ($inPlaceholders)
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

    $stmt = $db->prepare('INSERT INTO tuning_setup DEFAULT VALUES RETURNING id_tuning_setup');
    $stmt->execute();
    $setupId = (int)$stmt->fetchColumn();

    $stmt = $db->prepare('INSERT INTO tuning_setup_part (id_tuning_setup, id_tuning_part) VALUES (?, ?)');
    foreach ($partIds as $partId) {
        $stmt->execute([$setupId, $partId]);
    }

    $dryRun = finish_dry_run_transaction($db);
    echo json_encode(['success' => true, 'dryRun' => $dryRun, 'idTuningSetup' => $setupId]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('add_tuning_setup failed: ' . $e->getMessage());
}
?>
