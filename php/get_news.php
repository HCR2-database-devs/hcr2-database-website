<?php
$require_config = require_once __DIR__ . '/../auth/config.php';
require_once __DIR__ . '/maintenance_helpers.php';
enforce_maintenance_json();
header('Content-Type: application/json; charset=utf-8');
try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('get_news connection failed: ' . $e->getMessage());
}

$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 10;
if ($limit <= 0 || $limit > 100) $limit = 10;

try {
    if (db_column_exists($db, '_news', 'id')) {
        $sql = "
            SELECT id, title, content, author, created_at
            FROM (
                SELECT id::integer AS id, title, content, author, created_at::text AS created_at FROM news
                UNION ALL
                SELECT id::integer AS id, title, content, author, NULLIF(created_at, '') AS created_at FROM _news
            ) n
            ORDER BY COALESCE(created_at, '') DESC, id DESC
            LIMIT :limit
        ";
    } else {
        $sql = "
            SELECT id, title, content, author, created_at
            FROM news
            ORDER BY created_at DESC, id DESC
            LIMIT :limit
        ";
    }
    $stmt = $db->prepare($sql);
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode(['news' => $rows]);
} catch (PDOException $e) {
    generic_database_error('get_news failed: ' . $e->getMessage());
}
