<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('add_map connection failed: ' . $e->getMessage());
}

header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST ?? [];
}

$mapName = $data['mapName'] ?? null;

try {
    $db->beginTransaction();

    if (empty($mapName)) {
        $db->rollBack();
        echo json_encode(['error' => 'Map name is required.']);
        exit;
    }

    $mapName = trim($mapName);
    if (mb_strlen($mapName) > 19) {
        $db->rollBack();
        http_response_code(400);
        echo json_encode(['error' => 'Map name must be 19 characters or fewer.']);
        exit;
    }

    $check = $db->prepare('SELECT "idMap" FROM _map WHERE "nameMap" = :name LIMIT 1');
    $check->execute([':name' => $mapName]);
    if ($check->fetch()) {
        $db->rollBack();
        echo json_encode(['error' => 'Map already exists in database.']);
        exit;
    }

    if (db_column_has_default($db, '_map', 'idMap')) {
        $stmt = $db->prepare('INSERT INTO _map ("nameMap") VALUES (:nameMap) RETURNING "idMap"');
        $stmt->execute([':nameMap' => $mapName]);
        $newId = (int)$stmt->fetchColumn();
    } else {
        $newId = next_legacy_id($db, '_map', 'idMap');
        $stmt = $db->prepare('INSERT INTO _map ("idMap", "nameMap") VALUES (:idMap, :nameMap)');
        $stmt->execute([':idMap' => $newId, ':nameMap' => $mapName]);
    }

    $iconMessage = '';
    if (!empty($_FILES['icon']['tmp_name'])) {
        $iconFile = $_FILES['icon'];
        $fileName = $iconFile['name'];
        $mimeType = $iconFile['type'];
        
        if (!in_array($mimeType, ['image/svg+xml', 'text/plain']) && !preg_match('/\.svg$/i', $fileName)) {
            $db->rollBack();
            echo json_encode(['error' => 'Only SVG files are allowed for icons.']);
            exit;
        }
        
        if ($iconFile['size'] > 1048576) {
            $db->rollBack();
            echo json_encode(['error' => 'Icon file must be smaller than 1MB.']);
            exit;
        }
        
        $fileContent = file_get_contents($iconFile['tmp_name']);
        if (strpos($fileContent, '<svg') === false) {
            $db->rollBack();
            echo json_encode(['error' => 'File does not appear to be a valid SVG.']);
            exit;
        }
        
        $iconFilename = strtolower(str_replace(' ', '_', preg_replace('/[^a-zA-Z0-9 ]/', '', $mapName))) . '.svg';
        $iconPath = __DIR__ . '/../img/map_icons/' . $iconFilename;
        
        if (!is_dir(__DIR__ . '/../img/map_icons/')) {
            mkdir(__DIR__ . '/../img/map_icons/', 0755, true);
        }
        
        if (api_dry_run_enabled()) {
            $iconMessage = '(dry-run: icon upload skipped)';
        } elseif (move_uploaded_file($iconFile['tmp_name'], $iconPath)) {
            $iconMessage = '(icon uploaded: ' . $iconFilename . ')';
        } else {
            $iconMessage = '(warning: icon save failed)';
        }
    }

    $dryRun = finish_dry_run_transaction($db);
    echo json_encode(['success' => true, 'dryRun' => $dryRun, 'idMap' => $newId, 'nameMap' => $mapName, 'iconMessage' => $iconMessage]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('add_map failed: ' . $e->getMessage());
}
?>
