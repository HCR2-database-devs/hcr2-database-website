<?php

require_once __DIR__ . '/../auth/config.php';
require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();
header('Content-Type: application/json; charset=utf-8');

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('load_data connection failed: ' . $e->getMessage());
}

function get_data($db, $table, $select = '*', $where = '', $order = '', $limit = '') {
    $allowed_tables = ['_map', '_vehicle', '_player', '_tuningpart'];
    if (!in_array($table, $allowed_tables)) {
        return json_encode(array('error' => 'Invalid table'));
    }
    
    try {
        $sql = "SELECT $select FROM $table";
        if ($where) $sql .= " WHERE $where";
        if ($order) $sql .= " ORDER BY $order";
        if ($limit) $sql .= " LIMIT $limit";

        $stmt = $db->prepare($sql);
        $stmt->execute();
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        return json_encode($data);
    } catch (PDOException $e) {
        return json_encode(array('error' => 'Database error'));
    }
}

if (isset($_GET['type'])) {
    $type = $_GET['type'];
    switch ($type) {
        case 'maps':
            echo get_data($db, '_map');
            break;
        case 'vehicles':
            echo get_data($db, '_vehicle');
            break;
        case 'players':
            echo get_data($db, '_player');
            break;
        case 'tuning_parts':
            echo get_data($db, '_tuningpart', '*', '', 'nameTuningPart');
            break;
        case 'tuning_setups':
            $sql = "
                SELECT ts.idTuningSetup,
                       string_agg(tp.nameTuningPart, ', ') as parts
                FROM _tuningsetup ts
                JOIN _tuningsetupparts tsp ON ts.idTuningSetup = tsp.idTuningSetup
                JOIN _tuningpart tp ON tsp.idTuningPart = tp.idTuningPart
                GROUP BY ts.idTuningSetup
                ORDER BY ts.idTuningSetup
            ";
            $stmt = $db->prepare($sql);
            $stmt->execute();
            $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
            foreach ($data as &$row) {
                if ($row['parts'] !== null) {
                    $parts = explode(', ', $row['parts']);
                    $row['parts'] = array_map(function($name) {
                        return ['nameTuningPart' => $name];
                    }, $parts);
                } else {
                    $row['parts'] = [];
                }
            }
            echo json_encode($data);
            break;
        case 'records':
            $sql = "SELECT
                        wr.idRecord AS idRecord,
                        wr.distance,
                        wr.current,
                        wr.idTuningSetup,
                        wr.questionable,
                        COALESCE(wr.questionable_reason, '') as questionable_reason,
                        m.nameMap AS map_name,
                        v.nameVehicle AS vehicle_name,
                        p.namePlayer AS player_name,
                        p.country AS player_country,
                        string_agg(tp.nameTuningPart, ', ') as tuning_parts
                    FROM _worldrecord AS wr
                    JOIN _map AS m ON wr.idMap = m.idMap
                    JOIN _vehicle AS v ON wr.idVehicle = v.idVehicle
                    JOIN _player AS p ON wr.idPlayer = p.idPlayer
                    LEFT JOIN _tuningsetupparts tsp ON wr.idTuningSetup = tsp.idTuningSetup
                    LEFT JOIN _tuningpart tp ON tsp.idTuningPart = tp.idTuningPart
                    WHERE wr.current = 1
                    GROUP BY wr.idRecord, wr.distance, wr.current, wr.idTuningSetup, wr.questionable, wr.questionable_reason, m.nameMap, v.nameVehicle, p.namePlayer, p.country";
            $stmt = $db->prepare($sql);
            $stmt->execute();
            $records = $stmt->fetchAll(PDO::FETCH_ASSOC);
            echo json_encode($records);
            break;
        default:
            echo json_encode(array('error' => 'Invalid data type'));
    }
} else {
    echo json_encode(array('error' => 'No data type specified'));
}
?>