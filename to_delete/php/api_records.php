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
    $where[] = 'LOWER(m.nameMap) LIKE LOWER(:map)';
    $params[':map'] = safeLike($_GET['map']);
}
if (!empty($_GET['vehicle'])) {
    $where[] = 'LOWER(v.nameVehicle) LIKE LOWER(:vehicle)';
    $params[':vehicle'] = safeLike($_GET['vehicle']);
}
if (!empty($_GET['player'])) {
    $where[] = 'LOWER(p.namePlayer) LIKE LOWER(:player)';
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
    $where[] = '(LOWER(m.nameMap) LIKE LOWER(:q) OR LOWER(v.nameVehicle) LIKE LOWER(:q) OR LOWER(p.namePlayer) LIKE LOWER(:q) OR LOWER(wr.questionable_reason) LIKE LOWER(:q))';
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

$sql = "SELECT
        wr.idRecord as idRecord,
        wr.idMap,
        wr.idVehicle,
        wr.idPlayer,
        wr.distance,
        wr.current,
        wr.idTuningSetup,
        wr.questionable,
        COALESCE(wr.questionable_reason, '') as notes,
        m.nameMap as map_name,
        v.nameVehicle as vehicle_name,
        p.namePlayer as player_name,
        p.country as player_country,
        string_agg(tp.nameTuningPart, ', ') as tuning_parts
    FROM _worldrecord wr
    JOIN _map m ON wr.idMap = m.idMap
    JOIN _vehicle v ON wr.idVehicle = v.idVehicle
    LEFT JOIN _player p ON wr.idPlayer = p.idPlayer
    LEFT JOIN _tuningsetupparts tsp ON wr.idTuningSetup = tsp.idTuningSetup
    LEFT JOIN _tuningpart tp ON tsp.idTuningPart = tp.idTuningPart
    " . (count($where) ? 'WHERE ' . implode(' AND ', $where) : '') . "
    GROUP BY wr.idRecord, wr.idMap, wr.idVehicle, wr.idPlayer, wr.distance,
        wr.current, wr.idTuningSetup, wr.questionable, wr.questionable_reason,
        m.nameMap, v.nameVehicle, p.namePlayer, p.country
    ORDER BY wr.idRecord DESC
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
    http_response_code(500);
    echo json_encode(['error' => 'Database query failed']);
}
