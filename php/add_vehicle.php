<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('add_vehicle connection failed: ' . $e->getMessage());
}

header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST ?? [];
}

$vehicleName = $data['vehicleName'] ?? null;

try {
    $db->beginTransaction();

    if (empty($vehicleName)) {
        $db->rollBack();
        echo json_encode(['error' => 'Vehicle name is required.']);
        exit;
    }

    $vehicleName = trim($vehicleName);
    if (mb_strlen($vehicleName) > 16) {
        $db->rollBack();
        http_response_code(400);
        echo json_encode(['error' => 'Vehicle name must be 16 characters or fewer.']);
        exit;
    }

    $check = $db->prepare('SELECT id_vehicle FROM vehicle WHERE name_vehicle = :name LIMIT 1');
    $check->execute([':name' => $vehicleName]);
    if ($check->fetch()) {
        $db->rollBack();
        echo json_encode(['error' => 'Vehicle already exists in database.']);
        exit;
    }

    $stmt = $db->prepare('INSERT INTO vehicle (name_vehicle) VALUES (:nameVehicle) RETURNING id_vehicle');
    $stmt->execute([':nameVehicle' => $vehicleName]);
    $newId = (int)$stmt->fetchColumn();

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
        
        $iconFilename = strtolower(str_replace(' ', '_', preg_replace('/[^a-zA-Z0-9 ]/', '', $vehicleName))) . '.svg';
        $iconPath = __DIR__ . '/../img/vehicle_icons/' . $iconFilename;
        
        if (!is_dir(__DIR__ . '/../img/vehicle_icons/')) {
            mkdir(__DIR__ . '/../img/vehicle_icons/', 0755, true);
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
    echo json_encode(['success' => true, 'dryRun' => $dryRun, 'idVehicle' => $newId, 'nameVehicle' => $vehicleName, 'iconMessage' => $iconMessage]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('add_vehicle failed: ' . $e->getMessage());
}
?>
