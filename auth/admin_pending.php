<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();

header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = get_database_connection();
    $pdo->exec("CREATE TABLE IF NOT EXISTS PendingSubmission (
        id SERIAL PRIMARY KEY,
        idMap INTEGER,
        idVehicle INTEGER,
        distance INTEGER,
        playerName TEXT,
        playerCountry TEXT,
        submitterIp TEXT,
        status TEXT DEFAULT 'pending',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )");
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error']);
    exit;
} catch (Exception $e) {
}

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $stmt = $pdo->prepare("SELECT p.*, m.nameMap AS mapName, v.nameVehicle AS vehicleName FROM PendingSubmission p LEFT JOIN Map m ON p.idMap = m.idMap LEFT JOIN Vehicle v ON p.idVehicle = v.idVehicle WHERE p.status = 'pending' ORDER BY p.submitted_at DESC");
    $stmt->execute();
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode(['pending' => $rows]);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true) ?: $_POST;
$action = $data['action'] ?? null;
$id = isset($data['id']) ? (int)$data['id'] : null;

try {
    if ($action === 'approve') {
        if (!$id) throw new Exception('Missing id');

        $stmt = $pdo->prepare('SELECT * FROM PendingSubmission WHERE id = :id LIMIT 1');
        $stmt->execute([':id' => $id]);
        $sub = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$sub) throw new Exception('Submission not found');

        $pdo->beginTransaction();
        $del = $pdo->prepare('DELETE FROM WorldRecord WHERE idMap = :idMap AND idVehicle = :idVehicle');
        $del->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle']]);

        $playerId = null;
        if (!empty($sub['playerName'])) {
            $pstmt = $pdo->prepare('SELECT idPlayer FROM Player WHERE namePlayer = :name LIMIT 1');
            $pstmt->execute([':name' => $sub['playerName']]);
            $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
            if ($prow) {
                $playerId = (int)$prow['idPlayer'];
            } else {
                $row = $pdo->query('SELECT COALESCE(MAX(idPlayer), 0) AS m FROM Player')->fetch(PDO::FETCH_ASSOC);
                $newId = (int)$row['m'] + 1;
                $ins = $pdo->prepare('INSERT INTO Player (idPlayer, namePlayer, country) VALUES (:id, :name, :country)');
                $ins->execute([':id' => $newId, ':name' => $sub['playerName'], ':country' => $sub['playerCountry']]);
                $playerId = $newId;
            }
        }

        $ins = $pdo->prepare('INSERT INTO WorldRecord (idMap, idVehicle, idPlayer, distance, current) VALUES (:idMap, :idVehicle, :idPlayer, :distance, 1) RETURNING idRecord');
        $ins->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle'], ':idPlayer' => $playerId, ':distance' => $sub['distance']]);
        $recordRowid = $ins->fetchColumn();

        if (!empty($sub['tuningParts'])) {
            $tuningPartsStr = trim($sub['tuningParts']);
            if (!empty($tuningPartsStr)) {
                $partNames = array_map('trim', explode(',', $tuningPartsStr));
                $partNames = array_filter($partNames);

                if (count($partNames) >= 3 && count($partNames) <= 4) {
                    $partIds = [];
                    foreach ($partNames as $partName) {
                        $pstmt = $pdo->prepare('SELECT idTuningPart FROM TuningPart WHERE nameTuningPart = :name LIMIT 1');
                        $pstmt->execute([':name' => $partName]);
                        $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
                        if ($prow) {
                            $partIds[] = (int)$prow['idTuningPart'];
                        }
                    }

                    if (count($partIds) === count($partNames)) {
                        $row = $pdo->query('SELECT COALESCE(MAX(idTuningSetup), 0) AS m FROM TuningSetup')->fetch(PDO::FETCH_ASSOC);
                        $newSetupId = (int)$row['m'] + 1;

                        $setupStmt = $pdo->prepare('INSERT INTO TuningSetup (idTuningSetup) VALUES (:id)');
                        $setupStmt->execute([':id' => $newSetupId]);

                        $partStmt = $pdo->prepare('INSERT INTO TuningSetupParts (idTuningSetup, idTuningPart) VALUES (:setupId, :partId)');
                        foreach ($partIds as $partId) {
                            $partStmt->execute([':setupId' => $newSetupId, ':partId' => $partId]);
                        }

                        $updateStmt = $pdo->prepare('UPDATE WorldRecord SET idTuningSetup = :setupId WHERE idRecord = :idRecord');
                        $updateStmt->execute([':setupId' => $newSetupId, ':idRecord' => $recordRowid]);
                    }
                }
            }
        }

        $upd = $pdo->prepare("UPDATE PendingSubmission SET status = 'approved' WHERE id = :id");
        $upd->execute([':id' => $id]);

        $pdo->commit();
        echo json_encode(['success' => true]);
        exit;
    }

    if ($action === 'reject') {
        if (!$id) throw new Exception('Missing id');
        $upd = $pdo->prepare("UPDATE PendingSubmission SET status = 'rejected' WHERE id = :id");
        $upd->execute([':id' => $id]);
        echo json_encode(['success' => true]);
        exit;
    }

    echo json_encode(['error' => 'Unknown action']);
} catch (Exception $e) {
    if ($pdo && $pdo->inTransaction()) $pdo->rollBack();
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

?>
