<?php
define('RATE_LIMIT_REQUESTS', 30);
define('RATE_LIMIT_WINDOW', 60);
define('QUERY_TIMEOUT', 5);
define('RATE_LIMIT_FILE', sys_get_temp_dir() . '/api_rate_limit.json');

require_once __DIR__ . '/../auth/config.php';

header('Content-Type: application/json; charset=utf-8');

function check_rate_limit($apiKey) {
    $limits = [];
    if (file_exists(RATE_LIMIT_FILE)) {
        $limits = json_decode(file_get_contents(RATE_LIMIT_FILE), true) ?: [];
    }
    
    $now = time();
    $key = 'api_' . hash('sha256', $apiKey);

    foreach ($limits as $k => $v) {
        if ($v['reset'] < $now) {
            unset($limits[$k]);
        }
    }
    
    if (!isset($limits[$key])) {
        $limits[$key] = ['count' => 0, 'reset' => $now + RATE_LIMIT_WINDOW];
    }
    
    $limits[$key]['count']++;
    
    if ($limits[$key]['count'] > RATE_LIMIT_REQUESTS) {
        file_put_contents(RATE_LIMIT_FILE, json_encode($limits), LOCK_EX);
        return false;
    }
    
    file_put_contents(RATE_LIMIT_FILE, json_encode($limits), LOCK_EX);
    return true;
}

$headers = getallheaders();
$apiKey = $_GET['api_key'] ?? $headers['X-API-Key'] ?? $headers['x-api-key'] ?? null;
if (!$apiKey || !in_array($apiKey, $API_KEYS, true)) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized: invalid API key']);
    exit;
}

if (!check_rate_limit($apiKey)) {
    http_response_code(429);
    echo json_encode(['error' => 'Too many requests. Please try again later.']);
    exit;
}

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    error_log('api_records DB connection failed: ' . $e->getMessage());
    http_response_code(503);
    echo json_encode(['error' => 'Service temporarily unavailable']);
    exit;
} catch (Throwable $e) {
    error_log('api_records unexpected error: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error']);
    exit;
}

$params = [];
$where = ['wr.current = 1'];

function safeLike($value) {
    return '%' . str_replace(['%', '_'], ['\\%', '\\_'], $value) . '%';
}

// Log received parameters for debugging
error_log('api_records received params: ' . json_encode($_GET));

if (!empty($_GET['map'])) {
    $where[] = 'LOWER(m.name_map) = LOWER(:map)';
    $params[':map'] = $_GET['map'];
}

$vehicle = $_GET['vehicle'] ?? $_GET['car'] ?? null;
if (!empty($vehicle)) {
    $where[] = 'LOWER(v.name_vehicle) = LOWER(:vehicle)';
    $params[':vehicle'] = $vehicle;
}

if (!empty($_GET['player'])) {
    $where[] = 'LOWER(p.name_player) = LOWER(:player)';
    $params[':player'] = $_GET['player'];
}
if (!empty($_GET['country'])) {
    $where[] = 'LOWER(p.country) = LOWER(:country)';
    $params[':country'] = $_GET['country'];
}
if (isset($_GET['questionable']) && ($_GET['questionable'] === '0' || $_GET['questionable'] === '1')) {
    $where[] = 'wr.questionable = :questionable';
    $params[':questionable'] = (int)$_GET['questionable'];
}
if (isset($_GET['min_distance']) && is_numeric($_GET['min_distance'])) {
    $where[] = 'wr.distance >= :min_distance';
    $params[':min_distance'] = (int)$_GET['min_distance'];
}
if (isset($_GET['max_distance']) && is_numeric($_GET['max_distance'])) {
    $where[] = 'wr.distance <= :max_distance';
    $params[':max_distance'] = (int)$_GET['max_distance'];
}

if (!empty($_GET['q'])) {
    $q = safeLike($_GET['q']);
    $where[] = '(LOWER(m.name_map) LIKE LOWER(:q) OR LOWER(v.name_vehicle) LIKE LOWER(:q) OR LOWER(p.name_player) LIKE LOWER(:q) OR LOWER(wr.questionable_reason) LIKE LOWER(:q))';
    $params[':q'] = $q;
}

error_log('api_records final where clause: ' . implode(' AND ', $where));

$limit = 100;
if (isset($_GET['limit']) && is_numeric($_GET['limit'])) {
    $limit = (int)$_GET['limit'];
    if ($limit < 1) $limit = 1;
    if ($limit > 500) $limit = 500;
}
$offset = 0;
if (isset($_GET['offset']) && is_numeric($_GET['offset'])) {
    $offset = max(0, (int)$_GET['offset']);
}

$sql = "SELECT
        wr.id_map AS \"idMap\",
        wr.id_vehicle AS \"idVehicle\",
        wr.id_player AS \"idPlayer\",
        wr.distance,
        wr.current,
        wr.id_tuning_setup AS \"idTuningSetup\",
        wr.questionable,
        COALESCE(wr.questionable_reason, '') AS notes,
        m.name_map AS map_name,
        v.name_vehicle AS vehicle_name,
        p.name_player AS player_name,
        COALESCE(p.country, '') AS player_country,
        string_agg(tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part) AS tuning_parts
    FROM world_record wr
    JOIN map m ON wr.id_map = m.id_map
    JOIN vehicle v ON wr.id_vehicle = v.id_vehicle
    LEFT JOIN player p ON wr.id_player = p.id_player
    LEFT JOIN tuning_setup_part tsp ON wr.id_tuning_setup = tsp.id_tuning_setup
    LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
    " . (count($where) ? 'WHERE ' . implode(' AND ', $where) : '') . "
    GROUP BY
        wr.id_map,
        wr.id_vehicle,
        wr.id_player,
        wr.distance,
        wr.current,
        wr.id_tuning_setup,
        wr.questionable,
        wr.questionable_reason,
        m.name_map,
        v.name_vehicle,
        p.name_player,
        p.country
    ORDER BY wr.id_map DESC
    LIMIT :limit OFFSET :offset";

try {
    $stmt = $db->prepare($sql);
    
    foreach ($params as $k => $v) {
        $stmt->bindValue($k, $v, PDO::PARAM_STR);
    }
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
    
    $start_time = microtime(true);
    $stmt->execute();
    
    $elapsed = microtime(true) - $start_time;
    if ($elapsed > QUERY_TIMEOUT) {
        error_log("api_records query timeout: {$elapsed}s for parameters: " . json_encode($_GET));
        http_response_code(504);
        echo json_encode(['error' => 'Query timeout']);
        exit;
    }
    
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $response_size = strlen(json_encode($rows));
    if ($response_size > 10485760) {
        error_log("api_records response too large: {$response_size} bytes");
        http_response_code(413);
        echo json_encode(['error' => 'Response too large']);
        exit;
    }
    
    echo json_encode(['records' => $rows, 'count' => count($rows)]);
} catch (PDOException $e) {
    error_log('api_records query failed: ' . $e->getMessage());
    error_log('api_records SQL: ' . $sql);
    error_log('api_records WHERE clause: ' . implode(' AND ', $where));
    error_log('api_records params: ' . json_encode($params));
    http_response_code(503);
    echo json_encode(['error' => 'Database query failed']);
    exit;
} catch (Throwable $e) {
    error_log('api_records unexpected error: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Request failed']);
    exit;
}

$stmt = null;
$db = null;
