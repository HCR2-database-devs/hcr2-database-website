<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (Throwable $e) {
    generic_database_error('submit_record connection failed: ' . $e->getMessage());
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST ?? [];
}

$mapId = $data['mapId'] ?? null;
$vehicleId = $data['vehicleId'] ?? null;
$distance = $data['distance'] ?? null;
$playerId = $data['playerId'] ?? null;
$newPlayerName = $data['newPlayerName'] ?? null;
$country = $data['country'] ?? null;
$playerName = $data['playerName'] ?? null;
$tuningSetupId = $data['tuningSetupId'] ?? null;
$questionable = isset($data['questionable']) ? (int)$data['questionable'] : 0;
$note = $data['note'] ?? $data['questionableReason'] ?? null;

try {
    header('Content-Type: application/json; charset=utf-8');

    if (empty($mapId) || empty($vehicleId) || empty($distance)) {
        echo json_encode(['error' => 'Missing required fields (map, vehicle, or distance).']);
        exit;
    }

    $mapId = (int)$mapId;
    $vehicleId = (int)$vehicleId;
    if (!is_numeric($distance) || (int)$distance <= 0) {
        echo json_encode(['error' => 'Distance must be a positive number.']);
        exit;
    }
    $distance = (int)$distance;

    $db->beginTransaction();
    
    if (is_null($playerId) && empty($newPlayerName)) {
        $db->rollBack();
        echo json_encode(['error' => 'No valid player selected or provided.']);
        exit;
    }

    if (!is_null($playerId)) {
        $check = $db->prepare('SELECT 1 FROM _player WHERE "idPlayer" = :id LIMIT 1');
        $check->execute([':id' => $playerId]);
        if (!$check->fetch()) {
            $db->rollBack();
            echo json_encode(['error' => 'Selected player does not exist.']);
            exit;
        }
    }

    $playerId = is_null($playerId) || $playerId === '' ? null : (int)$playerId;
    if ($playerId === null && !empty($newPlayerName)) {
        $newPlayerName = trim((string)$newPlayerName);
        $country = trim((string)$country);
        if ($newPlayerName === '' || $country === '') {
            $db->rollBack();
            echo json_encode(['error' => 'New player name and country are required.']);
            exit;
        }
        if (mb_strlen($newPlayerName) > 15 || mb_strlen($country) > 32) {
            $db->rollBack();
            http_response_code(400);
            echo json_encode(['error' => 'Player name or country is too long for the database schema.']);
            exit;
        }

        if (db_column_has_default($db, '_player', 'idPlayer')) {
            $insertPlayer = $db->prepare('INSERT INTO _player ("namePlayer", country) VALUES (:name, :country) RETURNING "idPlayer"');
            $insertPlayer->execute([':name' => $newPlayerName, ':country' => $country]);
            $playerId = (int)$insertPlayer->fetchColumn();
        } else {
            $playerId = next_legacy_id($db, '_player', 'idPlayer');
            $insertPlayer = $db->prepare('INSERT INTO _player ("idPlayer", "namePlayer", country) VALUES (:id, :name, :country)');
            $insertPlayer->execute([':id' => $playerId, ':name' => $newPlayerName, ':country' => $country]);
        }
    }
    
    $stmt = $db->prepare('DELETE FROM _worldrecord WHERE "idMap" = :idMap AND "idVehicle" = :idVehicle');
    $stmt->execute([':idMap' => $mapId, ':idVehicle' => $vehicleId]);

    $insertSql = 'INSERT INTO _worldrecord ("idMap", "idVehicle", "idPlayer", distance, current, "idTuningSetup", questionable, questionable_reason) VALUES (:idMap, :idVehicle, :idPlayer, :distance, 1, :idTuningSetup, :questionable, :questionable_reason)';
    if (worldrecord_has_id_record($db)) {
        $insertSql .= ' RETURNING "idRecord"';
    }
    $stmt = $db->prepare($insertSql);
    $stmt->execute([':idMap' => $mapId, ':idVehicle' => $vehicleId, ':idPlayer' => $playerId, ':distance' => $distance, ':idTuningSetup' => $tuningSetupId, ':questionable' => $questionable, ':questionable_reason' => $note]);
    $recordId = worldrecord_has_id_record($db) ? (int)$stmt->fetchColumn() : $mapId . ':' . $vehicleId;

    $dryRun = finish_dry_run_transaction($db);

    $mapStmt = $db->prepare('SELECT "nameMap" FROM _map WHERE "idMap" = :idMap LIMIT 1');
    $mapStmt->execute([':idMap' => $mapId]);
    $mapRow = $mapStmt->fetch(PDO::FETCH_ASSOC);
    $mapName = $mapRow ? $mapRow['nameMap'] : 'Unknown';

    $vehicleStmt = $db->prepare('SELECT "nameVehicle" FROM _vehicle WHERE "idVehicle" = :idVehicle LIMIT 1');
    $vehicleStmt->execute([':idVehicle' => $vehicleId]);
    $vehicleRow = $vehicleStmt->fetch(PDO::FETCH_ASSOC);
    $vehicleName = $vehicleRow ? $vehicleRow['nameVehicle'] : 'Unknown';

    $playerName = 'Unknown';
    if (!is_null($playerId)) {
        $playerStmt = $db->prepare('SELECT "namePlayer" FROM _player WHERE "idPlayer" = :idPlayer LIMIT 1');
        $playerStmt->execute([':idPlayer' => $playerId]);
        $playerRow = $playerStmt->fetch(PDO::FETCH_ASSOC);
        $playerName = $playerRow ? $playerRow['namePlayer'] : 'Unknown';
    } elseif (!empty($newPlayerName)) {
        $playerName = $newPlayerName;
    }

    echo json_encode([
        'success' => true,
        'dryRun' => $dryRun,
        'recordId' => $recordId,
        'playerId' => $playerId,
        'mapName' => $mapName,
        'vehicleName' => $vehicleName,
        'playerName' => $playerName,
        'distance' => $distance
    ]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('submit_record failed: ' . $e->getMessage());
}
?>
