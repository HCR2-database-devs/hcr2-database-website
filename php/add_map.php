<?php
require_once __DIR__ . '/../auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    die(json_encode(array('error' => "Database connection failed: " . $e->getMessage())));
}

header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST ?? [];
}

$mapName = $data['mapName'] ?? null;

try {
    if (empty($mapName)) {
        echo json_encode(['error' => 'Map name is required.']);
        exit;
    }

    $mapName = trim($mapName);

    $check = $db->prepare('SELECT idMap FROM Map WHERE nameMap = :name LIMIT 1');
    $check->execute([':name' => $mapName]);
    if ($check->fetch()) {
        echo json_encode(['error' => 'Map already exists in database.']);
        exit;
    }

    $row = $db->query('SELECT COALESCE(MAX(idMap), 0) AS m FROM Map')->fetch(PDO::FETCH_ASSOC);
    $newId = (int)$row['m'] + 1;

    $stmt = $db->prepare('INSERT INTO Map (idMap, nameMap) VALUES (:idMap, :nameMap)');
    $stmt->execute([':idMap' => $newId, ':nameMap' => $mapName]);

    $iconMessage = '';
    if (!empty($_FILES['icon']['tmp_name'])) {
        $iconFile = $_FILES['icon'];
        $fileName = $iconFile['name'];
        $mimeType = $iconFile['type'];
        
        if (!in_array($mimeType, ['image/svg+xml', 'text/plain']) && !preg_match('/\.svg$/i', $fileName)) {
            echo json_encode(['error' => 'Only SVG files are allowed for icons.']);
            exit;
        }
        
        if ($iconFile['size'] > 1048576) {
            echo json_encode(['error' => 'Icon file must be smaller than 1MB.']);
            exit;
        }
        
        $fileContent = file_get_contents($iconFile['tmp_name']);
        if (strpos($fileContent, '<svg') === false) {
            echo json_encode(['error' => 'File does not appear to be a valid SVG.']);
            exit;
        }
        
        $iconFilename = strtolower(str_replace(' ', '_', preg_replace('/[^a-zA-Z0-9 ]/', '', $mapName))) . '.svg';
        $iconPath = __DIR__ . '/../img/map_icons/' . $iconFilename;
        
        if (!is_dir(__DIR__ . '/../img/map_icons/')) {
            mkdir(__DIR__ . '/../img/map_icons/', 0755, true);
        }
        
        if (move_uploaded_file($iconFile['tmp_name'], $iconPath)) {
            $iconMessage = '(icon uploaded: ' . $iconFilename . ')';
        } else {
            $iconMessage = '(warning: icon save failed)';
        }
    }

    echo json_encode(['success' => true, 'idMap' => $newId, 'nameMap' => $mapName, 'iconMessage' => $iconMessage]);
} catch (PDOException $e) {
    echo json_encode(['error' => "Database error: " . $e->getMessage()]);
}
?>