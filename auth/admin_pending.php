<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();

header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = get_database_connection();
} catch (Throwable $e) {
    generic_database_error('admin_pending connection failed: ' . $e->getMessage());
}

try {
    $pendingTable = pending_submissions_table($pdo);
} catch (Throwable $e) {
    generic_database_error('admin_pending table resolution failed: ' . $e->getMessage());
}

$method = $_SERVER['REQUEST_METHOD'];
$legacyPending = $pendingTable === '_pendingsubmission' || str_ends_with($pendingTable, '._pendingsubmission');

if ($method === 'GET') {
    try {
        if ($legacyPending) {
            $sql = 'SELECT p.*, m."nameMap" AS "mapName", v."nameVehicle" AS "vehicleName" FROM ' . $pendingTable . ' p LEFT JOIN _map m ON p."idMap" = m."idMap" LEFT JOIN _vehicle v ON p."idVehicle" = v."idVehicle" WHERE p.status = \'pending\' ORDER BY p.id DESC';
        } else {
            $sql = 'SELECT p.id, p.idmap AS "idMap", p.idvehicle AS "idVehicle", p.distance, p.playername AS "playerName", p.playercountry AS "playerCountry", p.submitterip AS "submitterIp", p.status, p.submitted_at, p.tuningparts AS "tuningParts", m."nameMap" AS "mapName", v."nameVehicle" AS "vehicleName" FROM ' . $pendingTable . ' p LEFT JOIN _map m ON p.idmap = m."idMap" LEFT JOIN _vehicle v ON p.idvehicle = v."idVehicle" WHERE p.status = \'pending\' ORDER BY p.submitted_at DESC, p.id DESC';
        }
        $stmt = $pdo->prepare($sql);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['pending' => $rows]);
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
        if (!$id) throw new Exception('Missing id');

        if ($legacyPending) {
            $stmt = $pdo->prepare("SELECT * FROM {$pendingTable} WHERE id = :id LIMIT 1");
        } else {
            $stmt = $pdo->prepare('SELECT id, idmap AS "idMap", idvehicle AS "idVehicle", distance, playername AS "playerName", playercountry AS "playerCountry", submitterip AS "submitterIp", status, submitted_at, tuningparts AS "tuningParts" FROM ' . $pendingTable . ' WHERE id = :id LIMIT 1');
        }
        $stmt->execute([':id' => $id]);
        $sub = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$sub) throw new Exception('Submission not found');

        $pdo->beginTransaction();
        $del = $pdo->prepare('DELETE FROM _worldrecord WHERE "idMap" = :idMap AND "idVehicle" = :idVehicle');
        $del->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle']]);

        $playerId = null;
        if (!empty($sub['playerName'])) {
            $pstmt = $pdo->prepare('SELECT "idPlayer" FROM _player WHERE "namePlayer" = :name LIMIT 1');
            $pstmt->execute([':name' => $sub['playerName']]);
            $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
            if ($prow) {
                $playerId = (int)$prow['idPlayer'];
            } else {
                if (db_column_has_default($pdo, '_player', 'idPlayer')) {
                    $ins = $pdo->prepare('INSERT INTO _player ("namePlayer", country) VALUES (:name, :country) RETURNING "idPlayer"');
                    $ins->execute([':name' => $sub['playerName'], ':country' => $sub['playerCountry']]);
                    $playerId = (int)$ins->fetchColumn();
                } else {
                    $playerId = next_legacy_id($pdo, '_player', 'idPlayer');
                    $ins = $pdo->prepare('INSERT INTO _player ("idPlayer", "namePlayer", country) VALUES (:id, :name, :country)');
                    $ins->execute([':id' => $playerId, ':name' => $sub['playerName'], ':country' => $sub['playerCountry']]);
                }
            }
        }

        $insertRecordSql = 'INSERT INTO _worldrecord ("idMap", "idVehicle", "idPlayer", distance, current) VALUES (:idMap, :idVehicle, :idPlayer, :distance, 1)';
        if (worldrecord_has_id_record($pdo)) {
            $insertRecordSql .= ' RETURNING "idRecord"';
        }
        $ins = $pdo->prepare($insertRecordSql);
        $ins->execute([':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle'], ':idPlayer' => $playerId, ':distance' => $sub['distance']]);
        $recordId = worldrecord_has_id_record($pdo) ? (int)$ins->fetchColumn() : null;

        if (!empty($sub['tuningParts'])) {
            $tuningPartsStr = trim($sub['tuningParts']);
            if (!empty($tuningPartsStr)) {
                $partNames = array_map('trim', explode(',', $tuningPartsStr));
                $partNames = array_filter($partNames);

                if (count($partNames) >= 3 && count($partNames) <= 4) {
                    $partIds = [];
                    foreach ($partNames as $partName) {
                        $pstmt = $pdo->prepare('SELECT "idTuningPart" FROM _tuningpart WHERE "nameTuningPart" = :name LIMIT 1');
                        $pstmt->execute([':name' => $partName]);
                        $prow = $pstmt->fetch(PDO::FETCH_ASSOC);
                        if ($prow) {
                            $partIds[] = (int)$prow['idTuningPart'];
                        }
                    }

                    if (count($partIds) === count($partNames)) {
                        if (db_column_has_default($pdo, '_tuningsetup', 'idTuningSetup')) {
                            $setupStmt = $pdo->prepare('INSERT INTO _tuningsetup DEFAULT VALUES RETURNING "idTuningSetup"');
                            $setupStmt->execute();
                            $newSetupId = (int)$setupStmt->fetchColumn();
                        } else {
                            $newSetupId = next_legacy_id($pdo, '_tuningsetup', 'idTuningSetup');
                            $setupStmt = $pdo->prepare('INSERT INTO _tuningsetup ("idTuningSetup") VALUES (:id)');
                            $setupStmt->execute([':id' => $newSetupId]);
                        }

                        $partStmt = $pdo->prepare('INSERT INTO _tuningsetupparts ("idTuningSetup", "idTuningPart") VALUES (:setupId, :partId)');
                        foreach ($partIds as $partId) {
                            $partStmt->execute([':setupId' => $newSetupId, ':partId' => $partId]);
                        }

                        if (worldrecord_has_id_record($pdo)) {
                            $updateStmt = $pdo->prepare('UPDATE _worldrecord SET "idTuningSetup" = :setupId WHERE "idRecord" = :idRecord');
                            $updateStmt->execute([':setupId' => $newSetupId, ':idRecord' => $recordId]);
                        } else {
                            $updateStmt = $pdo->prepare('UPDATE _worldrecord SET "idTuningSetup" = :setupId WHERE "idMap" = :idMap AND "idVehicle" = :idVehicle AND current = 1');
                            $updateStmt->execute([':setupId' => (string)$newSetupId, ':idMap' => $sub['idMap'], ':idVehicle' => $sub['idVehicle']]);
                        }
                    }
                }
            }
        }

        $upd = $pdo->prepare("UPDATE {$pendingTable} SET status = 'approved' WHERE id = :id");
        $upd->execute([':id' => $id]);

        $dryRun = finish_dry_run_transaction($pdo);
        echo json_encode(['success' => true, 'dryRun' => $dryRun]);
        exit;
    }

    if ($action === 'reject') {
        if (!$id) throw new Exception('Missing id');
        $pdo->beginTransaction();
        $upd = $pdo->prepare("UPDATE {$pendingTable} SET status = 'rejected' WHERE id = :id");
        $upd->execute([':id' => $id]);
        $dryRun = finish_dry_run_transaction($pdo);
        echo json_encode(['success' => true, 'dryRun' => $dryRun]);
        exit;
    }

    echo json_encode(['error' => 'Unknown action']);
} catch (Exception $e) {
    if ($pdo && $pdo->inTransaction()) $pdo->rollBack();
    generic_database_error('admin_pending failed: ' . $e->getMessage());
}

?>
