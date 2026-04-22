<?php
if (!function_exists('safe_json_error')) {
    function safe_json_error(string $message, int $statusCode = 500): void {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
            http_response_code($statusCode);
        }
        echo json_encode(['error' => $message]);
        exit;
    }
}

try {
    require_once __DIR__ . '/../auth/config.php';
} catch (Throwable $e) {
    safe_json_error('Server configuration error');
}

require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();
header('Content-Type: application/json; charset=utf-8');

try {
    $db = get_database_connection();
} catch (Throwable $e) {
    generic_database_error('load_data connection failed: ' . $e->getMessage());
}

function get_data($db, $table, $select = '*', $where = '', $order = '', $limit = '') {
    $allowed_tables = ['map', 'vehicle', 'player', 'tuning_part'];
    if (!in_array($table, $allowed_tables, true)) {
        return json_encode(['error' => 'Invalid table']);
    }
    
    try {
        $sql = "SELECT $select FROM $table";
        if ($where) {
            $sql .= " WHERE $where";
        }
        if ($order) {
            $sql .= " ORDER BY $order";
        }
        if ($limit) {
            $sql .= " LIMIT $limit";
        }

        $stmt = $db->prepare($sql);
        $stmt->execute();
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        return json_encode($data);
    } catch (Throwable $e) {
        error_log("Database error in get_data for table $table: " . $e->getMessage());
        return json_encode(['error' => 'Database error', 'details' => $e->getMessage()]);
    }
}

if (isset($_GET['type'])) {
    $type = $_GET['type'];
    switch ($type) {
        case 'maps':
            echo get_data($db, 'map');
            break;
        case 'vehicles':
            echo get_data($db, 'vehicle');
            break;
        case 'players':
            echo get_data($db, 'player');
            break;
        case 'tuning_parts':
            echo get_data($db, 'tuning_part', '*', '', 'name_tuning_part');
            break;
        case 'tuning_setups':
            try {
                $sql = "
                    SELECT ts.id_tuning_setup AS \"idTuningSetup\",
                           string_agg(tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part) AS parts
                    FROM tuning_setup ts
                    LEFT JOIN tuning_setup_part tsp ON ts.id_tuning_setup = tsp.id_tuning_setup
                    LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
                    GROUP BY ts.id_tuning_setup
                    ORDER BY ts.id_tuning_setup
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
            } catch (Throwable $e) {
                error_log('load_data tuning_setups failed: ' . $e->getMessage());
                generic_database_error('load_data tuning_setups failed: ' . $e->getMessage());
            }
            break;
        case 'records':
            try {
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
                            COALESCE(wr.questionable_reason, '') AS questionable_reason,
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
                        WHERE wr.current = 1
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
                        ORDER BY wr.id_map DESC";
                $stmt = $db->prepare($sql);
                $stmt->execute();
                $records = $stmt->fetchAll(PDO::FETCH_ASSOC);
                echo json_encode($records);
            } catch (Throwable $e) {
                error_log('load_data records failed: ' . $e->getMessage());
                generic_database_error('load_data records failed: ' . $e->getMessage());
            }
            break;
        default:
            echo json_encode(['error' => 'Invalid data type']);
    }
} else {
    echo json_encode(['error' => 'No data type specified']);
}
?>
