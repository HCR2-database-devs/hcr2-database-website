<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();

header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = get_database_connection();
} catch (Throwable $e) {
    generic_database_error('admin_pending connection failed: ' . $e->getMessage());
}

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    try {
        $sql = '
            SELECT
                p.id,
                p.id_map AS "idMap",
                p.id_vehicle AS "idVehicle",
                p.distance,
                p.player_name AS "playerName",
                p.player_country AS "playerCountry",
                p.submitter_ip AS "submitterIp",
                p.status,
                p.submitted_at,
                p.tuning_parts AS "tuningParts",
                m.name_map AS "mapName",
                v.name_vehicle AS "vehicleName"
            FROM pending_submission p
            LEFT JOIN map m ON p.id_map = m.id_map
            LEFT JOIN vehicle v ON p.id_vehicle = v.id_vehicle
            WHERE p.status = \'pending\'
            ORDER BY p.submitted_at DESC, p.id DESC
        ';
        $stmt = $pdo->prepare($sql);
        $stmt->execute();
        echo json_encode(['pending' => $stmt->fetchAll(PDO::FETCH_ASSOC)]);
        exit;
    } catch (Throwable $e) {
        generic_database_error('admin_pending GET failed: ' . $e->getMessage());
    }
}

$data = json_decode(file_get_contents('php://input'), true) ?: $_POST;
$action = $data['action'] ?? null;
$id = isset($data['id']) ? (int)$data['id'] : null;

try {
    if ($action === 'approve') {
        if (!$id) {
            throw new RuntimeException('Missing id');
        }

        $stmt = $pdo->prepare('
            SELECT
                id,
                id_map AS "idMap",
                id_vehicle AS "idVehicle",
                distance,
                player_name AS "playerName",
                player_country AS "playerCountry",
                submitter_ip AS "submitterIp",
                status,
                submitted_at,
                tuning_parts AS "tuningParts"
            FROM pending_submission
            WHERE id = :id
            LIMIT 1
        ');
        $stmt->execute([':id' => $id]);
        $sub = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$sub) {
            throw new RuntimeException('Submission not found');
        }

        $pdo->beginTransaction();

        $del = $pdo->prepare('DELETE FROM world_record WHERE id_map = :idMap AND id_vehicle = :idVehicle');
        $del->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle']]);

        $playerId = null;
        if (!empty($sub['playerName'])) {
            $pstmt = $pdo->prepare('SELECT id_player FROM player WHERE name_player = :name LIMIT 1');
            $pstmt->execute([':name' => $sub['playerName']]);
            $playerId = $pstmt->fetchColumn();

            if ($playerId === false) {
                $ins = $pdo->prepare('INSERT INTO player (name_player, country) VALUES (:name, :country) RETURNING id_player');
                $ins->execute([
                    ':name' => $sub['playerName'],
                    ':country' => (string)$sub['playerCountry'],
                ]);
                $playerId = $ins->fetchColumn();
            }

            $playerId = (int)$playerId;
        }

        $ins = $pdo->prepare('INSERT INTO world_record (id_map, id_vehicle, id_player, distance, current) VALUES (:idMap, :idVehicle, :idPlayer, :distance, 1) RETURNING id_record');
        $ins->execute([
            ':idMap' => $sub['idMap'],
            ':idVehicle' => $sub['idVehicle'],
            ':idPlayer' => $playerId,
            ':distance' => $sub['distance'],
        ]);
        $recordId = (int)$ins->fetchColumn();

        if (!empty($sub['tuningParts'])) {
            $tuningPartsStr = trim((string)$sub['tuningParts']);
            if ($tuningPartsStr !== '') {
                $partNames = array_values(array_filter(array_map('trim', explode(',', $tuningPartsStr))));

                if (count($partNames) >= 3 && count($partNames) <= 4) {
                    $partIds = [];
                    foreach ($partNames as $partName) {
                        $pstmt = $pdo->prepare('SELECT id_tuning_part FROM tuning_part WHERE name_tuning_part = :name LIMIT 1');
                        $pstmt->execute([':name' => $partName]);
                        $found = $pstmt->fetchColumn();
                        if ($found === false) {
                            $partIds = [];
                            break;
                        }
                        $partIds[] = (int)$found;
                    }

                    if (count($partIds) === count($partNames)) {
                        $setupStmt = $pdo->prepare('INSERT INTO tuning_setup DEFAULT VALUES RETURNING id_tuning_setup');
                        $setupStmt->execute();
                        $newSetupId = (int)$setupStmt->fetchColumn();

                        $partStmt = $pdo->prepare('INSERT INTO tuning_setup_part (id_tuning_setup, id_tuning_part) VALUES (:setupId, :partId)');
                        foreach ($partIds as $partId) {
                            $partStmt->execute([':setupId' => $newSetupId, ':partId' => $partId]);
                        }

                        $updateStmt = $pdo->prepare('UPDATE world_record SET id_tuning_setup = :setupId WHERE id_record = :idRecord');
                        $updateStmt->execute([':setupId' => $newSetupId, ':idRecord' => $recordId]);
                    }
                }
            }
        }

        $upd = $pdo->prepare("UPDATE pending_submission SET status = 'approved' WHERE id = :id");
        $upd->execute([':id' => $id]);

        $dryRun = finish_dry_run_transaction($pdo);
        echo json_encode(['success' => true, 'dryRun' => $dryRun]);
        exit;
    }

    if ($action === 'reject') {
        if (!$id) {
            throw new RuntimeException('Missing id');
        }
        $pdo->beginTransaction();
        $upd = $pdo->prepare("UPDATE pending_submission SET status = 'rejected' WHERE id = :id");
        $upd->execute([':id' => $id]);
        $dryRun = finish_dry_run_transaction($pdo);
        echo json_encode(['success' => true, 'dryRun' => $dryRun]);
        exit;
    }

    echo json_encode(['error' => 'Unknown action']);
} catch (Throwable $e) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    generic_database_error('admin_pending failed: ' . $e->getMessage());
}
