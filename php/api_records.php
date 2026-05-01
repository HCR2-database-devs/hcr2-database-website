<?php
require_once __DIR__ . '/../auth/config.php';

header('Content-Type: application/json; charset=utf-8');

$headers = getallheaders();
$apiKey = $_GET['api_key'] ?? $headers['X-API-Key'] ?? $headers['x-api-key'] ?? null;
if (!$apiKey || !in_array($apiKey, $API_KEYS, true)) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized: invalid API key']);
    exit;
}

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

$params = [];
$where = ['wr.current = 1'];

function safeLike($value) {
    return '%' . str_replace(['%', '_'], ['\\%', '\\_'], $value) . '%';
}

if (!empty($_GET['map'])) {
    $where[] = 'LOWER(m.name_map) LIKE LOWER(:map)';
    $params[':map'] = safeLike($_GET['map']);
}
if (!empty($_GET['vehicle'])) {
    $where[] = 'LOWER(v.name_vehicle) LIKE LOWER(:vehicle)';
    $params[':vehicle'] = safeLike($_GET['vehicle']);
}
if (!empty($_GET['player'])) {
    $where[] = 'LOWER(p.name_player) LIKE LOWER(:player)';
    $params[':player'] = safeLike($_GET['player']);
}
if (!empty($_GET['country'])) {
    $where[] = 'LOWER(p.country) LIKE LOWER(:country)';
    $params[':country'] = safeLike($_GET['country']);
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

$setupJoin = 'wr.id_tuning_setup = tsp.id_tuning_setup';

$sql = "SELECT
        " . record_key_sql('wr') . " AS \"idRecord\",
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
    LEFT JOIN tuning_setup_part tsp ON {$setupJoin}
    LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
    " . (count($where) ? 'WHERE ' . implode(' AND ', $where) : '') . "
    GROUP BY
        wr.id_record,
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

$stmt = $db->prepare($sql);
foreach ($params as $k => $v) {
    $stmt->bindValue($k, $v, PDO::PARAM_STR);
}
$stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
$stmt->bindValue(':offset', $offset, PDO::PARAM_INT);

try {
    $stmt->execute();
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode(['records' => $rows, 'count' => count($rows)]);
} catch (PDOException $e) {
    error_log('api_records query failed: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Database query failed', 'details' => $e->getMessage()]);
}
