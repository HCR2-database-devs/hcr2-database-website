<?php
require_once __DIR__ . '/../auth/config.php';
require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();

header('Content-Type: application/json; charset=utf-8');

function verify_hcaptcha($token, $secret) {
    if (empty($token) || empty($secret)) {
        return false;
    }
    $url = 'https://hcaptcha.com/siteverify';
    $postFields = http_build_query([
        'secret' => $secret,
        'response' => $token
    ]);

    if (function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postFields);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200 || !$response) {
            return false;
        }

        $result = json_decode($response, true);
        return isset($result['success']) && $result['success'] === true;
    }

    if (ini_get('allow_url_fopen')) {
        $opts = [
            'http' => [
                'method'  => 'POST',
                'header'  => "Content-type: application/x-www-form-urlencoded\r\n",
                'content' => $postFields,
                'timeout' => 5
            ],
            'ssl' => [
                'verify_peer' => true,
                'verify_peer_name' => true,
            ]
        ];
        $context = stream_context_create($opts);
        $response = @file_get_contents($url, false, $context);
        if ($response === false) {
            return false;
        }
        $result = json_decode($response, true);
        return isset($result['success']) && $result['success'] === true;
    }

    error_log('verify_hcaptcha: no HTTP client available (curl missing and allow_url_fopen disabled)');
    return false;
}

try {
    $db = get_database_connection();
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

try {
    $pendingTable = pending_submissions_table($db);
} catch (Throwable $e) {
    generic_database_error('public_submit table resolution failed: ' . $e->getMessage());
}


$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) $data = $_POST ?? [];

$hcaptcha_response = isset($data['h_captcha_response']) ? trim($data['h_captcha_response']) : '';

$mapId = isset($data['mapId']) ? (int)$data['mapId'] : null;
$vehicleId = isset($data['vehicleId']) ? (int)$data['vehicleId'] : null;
$distance = isset($data['distance']) ? (int)$data['distance'] : null;
$playerName = isset($data['playerName']) ? trim($data['playerName']) : '';
$playerCountry = isset($data['playerCountry']) ? trim($data['playerCountry']) : '';

$honeypot_email = isset($data['hp_email']) ? trim($data['hp_email']) : '';
$honeypot_website = isset($data['hp_website']) ? trim($data['hp_website']) : '';
$honeypot_phone = isset($data['hp_phone']) ? trim($data['hp_phone']) : '';
$honeypot_comments = isset($data['hp_comments']) ? trim($data['hp_comments']) : '';
$form_load_time = isset($data['form_load_time']) ? (int)$data['form_load_time'] : 0;
$submission_time = isset($data['submission_time']) ? (int)$data['submission_time'] : 0;
$tuningParts = isset($data['tuningParts']) ? $data['tuningParts'] : [];
if (!is_array($tuningParts)) {
    if (is_string($tuningParts)) {
        $tuningParts = array_filter(array_map('trim', explode(',', $tuningParts)));
    } else {
        $tuningParts = [];
    }
}

if (!verify_hcaptcha($hcaptcha_response, $HCAPTCHA_SECRET_KEY)) {
    http_response_code(400);
    echo json_encode(['error' => 'hCaptcha verification failed. Please try again.']);
    exit;
}

if (empty($mapId) || empty($vehicleId) || empty($distance) || empty($playerName)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields (map, vehicle, distance, or player name).']);
    exit;
}

if (!empty($honeypot_email) || !empty($honeypot_website) || !empty($honeypot_phone) || !empty($honeypot_comments)) {
    http_response_code(400);
    echo json_encode(['error' => 'Spam detected']);
    exit;
}

if ($form_load_time > 0 && $submission_time > 0) {
    $time_spent = $submission_time - $form_load_time;
    if ($time_spent < 2000) {
        http_response_code(429);
        echo json_encode(['error' => 'Please take your time to fill out the form. Submissions that are too fast are rejected.']);
        exit;
    }
    if ($time_spent < 1000) {
        http_response_code(400);
        echo json_encode(['error' => 'Spam detected']);
        exit;
    }
}

if ($distance <= 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Distance must be a positive number.']);
    exit;
}
if (count($tuningParts) < 3 || count($tuningParts) > 4) {
    http_response_code(400);
    echo json_encode(['error' => 'Please provide 3 or 4 tuning parts for the record.']);
    exit;
}
try {
    $ip = $_SERVER['REMOTE_ADDR'] ?? '';
    if ($ip) {
        $rstmt = $db->prepare("SELECT COUNT(1) AS c FROM {$pendingTable} WHERE submitterIp = :ip AND submitted_at >= NOW() - INTERVAL '1 hour'");
        $rstmt->execute([':ip' => $ip]);
        $rc = $rstmt->fetch(PDO::FETCH_ASSOC);
        if ($rc && isset($rc['c']) && (int)$rc['c'] >= 5) {
            http_response_code(429);
            echo json_encode(['error' => 'Rate limit exceeded. Please try again later.']);
            exit;
        }
    }
    $stmt = $db->prepare("INSERT INTO {$pendingTable} (idMap, idVehicle, distance, playerName, playerCountry, tuningParts, submitterIp) VALUES (:idMap, :idVehicle, :distance, :playerName, :playerCountry, :tuningParts, :ip)");
    $stmt->execute([
        ':idMap' => $mapId,
        ':idVehicle' => $vehicleId,
        ':distance' => $distance,
        ':playerName' => $playerName,
        ':playerCountry' => $playerCountry,
        ':tuningParts' => implode(', ', $tuningParts),
        ':ip' => $_SERVER['REMOTE_ADDR'] ?? ''
    ]);

    echo json_encode(['success' => true, 'message' => 'Submission received and is pending review by admins.']);
} catch (PDOException $e) {
    generic_database_error('public_submit failed: ' . $e->getMessage());
}

?>
