<?php
define('QUERY_TIMEOUT', 5); // seconds

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
    safe_json_error('Server configuration error', 500);
}

require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();
header('Content-Type: application/json; charset=utf-8');

try {
    $db = get_database_connection();
} catch (Throwable $e) {
    error_log('load_data connection failed: ' . $e->getMessage());
    safe_json_error('Service temporarily unavailable', 503);
}

function get_data($db, $table, $select = '*', $where = '', $order = '', $limit = '') {
    $allowed_tables = ['_map', '_vehicle', '_player', '_tuningpart'];
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
        $start_time = microtime(true);
        $stmt->execute();
        
        $elapsed = microtime(true) - $start_time;
        if ($elapsed > QUERY_TIMEOUT) {
            error_log("load_data query timeout for table $table: {$elapsed}s");
            return json_encode(['error' => 'Query timeout']);
        }
        
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        return json_encode($data);
    } catch (Throwable $e) {
        error_log("Database error in get_data for table $table: " . $e->getMessage());
        return json_encode(['error' => 'Database error']);
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
            echo get_data($db, '_tuningpart', '*', '', '"nameTuningPart"');
            break;
        case 'tuning_setups':
            try {
                $sql = "
                    SELECT ts.\"idTuningSetup\" AS \"idTuningSetup\",
                           string_agg(tp.\"nameTuningPart\", ', ' ORDER BY tp.\"nameTuningPart\") AS parts
                    FROM _tuningsetup ts
                    LEFT JOIN _tuningsetupparts tsp ON ts.\"idTuningSetup\" = tsp.\"idTuningSetup\"
                    LEFT JOIN _tuningpart tp ON tsp.\"idTuningPart\" = tp.\"idTuningPart\"
                    GROUP BY ts.\"idTuningSetup\"
                    ORDER BY ts.\"idTuningSetup\"
                ";
                $stmt = $db->prepare($sql);
                $start_time = microtime(true);
                $stmt->execute();
                
                $elapsed = microtime(true) - $start_time;
                if ($elapsed > QUERY_TIMEOUT) {
                    error_log("load_data tuning_setups timeout: {$elapsed}s");
                    safe_json_error('Query timeout', 504);
                }
                
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
                safe_json_error('Database error', 503);
            }
            break;
        case 'records':
            try {
                $sql = "SELECT
                            wr.\"idMap\",
                            wr.\"idVehicle\",
                            wr.\"idPlayer\",
                            wr.distance,
                            wr.current,
                            wr.\"idTuningSetup\",
                            wr.questionable,
                            COALESCE(wr.questionable_reason, '') AS questionable_reason,
                            m.\"nameMap\" AS map_name,
                            v.\"nameVehicle\" AS vehicle_name,
                            p.\"namePlayer\" AS player_name,
                            COALESCE(p.country, '') AS player_country,
                            string_agg(tp.\"nameTuningPart\", ', ' ORDER BY tp.\"nameTuningPart\") AS tuning_parts
                        FROM _worldrecord wr
                        JOIN _map m ON wr.\"idMap\" = m.\"idMap\"
                        JOIN _vehicle v ON wr.\"idVehicle\" = v.\"idVehicle\"
                        LEFT JOIN _player p ON wr.\"idPlayer\" = p.\"idPlayer\"
                        LEFT JOIN _tuningsetupparts tsp ON CAST(wr.\"idTuningSetup\" AS smallint) = tsp.\"idTuningSetup\"
                        LEFT JOIN _tuningpart tp ON tsp.\"idTuningPart\" = tp.\"idTuningPart\"
                        WHERE wr.current = 1
                        GROUP BY
                            wr.\"idMap\",
                            wr.\"idVehicle\",
                            wr.\"idPlayer\",
                            wr.distance,
                            wr.current,
                            wr.\"idTuningSetup\",
                            wr.questionable,
                            wr.questionable_reason,
                            m.\"nameMap\",
                            v.\"nameVehicle\",
                            p.\"namePlayer\",
                            p.country,
                            wr.\"idPlayer\"
                        ORDER BY wr.\"idMap\" DESC";
                $stmt = $db->prepare($sql);
                $start_time = microtime(true);
                $stmt->execute();
                
                $elapsed = microtime(true) - $start_time;
                if ($elapsed > QUERY_TIMEOUT) {
                    error_log("load_data records timeout: {$elapsed}s");
                    safe_json_error('Query timeout', 504);
                }
                
                $records = $stmt->fetchAll(PDO::FETCH_ASSOC);
                echo json_encode($records);
            } catch (Throwable $e) {
                error_log('load_data records failed: ' . $e->getMessage());

// Clean up resources
$stmt = null;
$db = null;
                safe_json_error('Database error', 503);
            }
            break;
        default:
            echo json_encode(['error' => 'Invalid data type']);
    }
} else {
    echo json_encode(['error' => 'No data type specified']);
}
?>
