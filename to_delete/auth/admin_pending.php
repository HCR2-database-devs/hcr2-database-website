<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();

header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('admin_pending connection failed: ' . $e->getMessage());
}

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $stmt = $pdo->prepare("SELECT p.*, m.nameMap AS mapName, v.nameVehicle AS vehicleName FROM PendingSubmission p LEFT JOIN _map m ON p.idMap = m.idMap LEFT JOIN _vehicle v ON p.idVehicle = v.idVehicle WHERE p.status = 'pending' ORDER BY p.submitted_at DESC");
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
        $del = $pdo->prepare('DELETE FROM _worldrecord WHERE idMap = :idMap AND idVehicle = :idVehicle');
        $del->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle']]);

        $playerId = null;
        if (!empty($sub['playerName'])) {
            $pstmt = $pdo->prepare('SELECT idPlayer FROM _player WHERE namePlayer = :name LIMIT 1');
            $pstmt->execute([':name' => $sub['playerName']]);
            $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
            if ($prow) {
                $playerId = (int)$prow['idPlayer'];
            } else {
                $row = $pdo->query('SELECT COALESCE(MAX(idPlayer), 0) AS m FROM _player')->fetch(PDO::FETCH_ASSOC);
                $newId = (int)$row['m'] + 1;
                $ins = $pdo->prepare('INSERT INTO _player (idPlayer, namePlayer, country) VALUES (:id, :name, :country)');
                $ins->execute([':id' => $newId, ':name' => $sub['playerName'], ':country' => $sub['playerCountry']]);
                $playerId = $newId;
            }
        }

        $ins = $pdo->prepare('INSERT INTO _worldrecord (idMap, idVehicle, idPlayer, distance, current) VALUES (:idMap, :idVehicle, :idPlayer, :distance, 1) RETURNING idRecord');
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
                        $pstmt = $pdo->prepare('SELECT idTuningPart FROM _tuningpart WHERE nameTuningPart = :name LIMIT 1');
                        $pstmt->execute([':name' => $partName]);
                        $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
                        if ($prow) {
                            $partIds[] = (int)$prow['idTuningPart'];
                        }
                    }

                    if (count($partIds) === count($partNames)) {
                        $row = $pdo->query('SELECT COALESCE(MAX(idTuningSetup), 0) AS m FROM _tuningsetup')->fetch(PDO::FETCH_ASSOC);
                        $newSetupId = (int)$row['m'] + 1;

                        $setupStmt = $pdo->prepare('INSERT INTO _tuningsetup (idTuningSetup) VALUES (:id)');
                        $setupStmt->execute([':id' => $newSetupId]);

                        $partStmt = $pdo->prepare('INSERT INTO _tuningsetupparts (idTuningSetup, idTuningPart) VALUES (:setupId, :partId)');
                        foreach ($partIds as $partId) {
                            $partStmt->execute([':setupId' => $newSetupId, ':partId' => $partId]);
                        }

                        $updateStmt = $pdo->prepare('UPDATE _worldrecord SET idTuningSetup = :setupId WHERE idRecord = :idRecord');
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
    generic_database_error('admin_pending failed: ' . $e->getMessage());
}

?>
