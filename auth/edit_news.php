<?php
require_once __DIR__ . '/check_auth.php';
ensure_authorized_json();
header('Content-Type: application/json; charset=utf-8');

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('edit_news connection failed: ' . $e->getMessage());
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

$id = isset($data['id']) ? (int)$data['id'] : 0;
$title = isset($data['title']) ? trim($data['title']) : '';
$content = isset($data['content']) ? trim($data['content']) : '';

if ($id <= 0 || $title === '' || $content === '') {
    http_response_code(400);
    echo json_encode(['error' => 'News ID, title, and content are required.']);
    exit;
}

$title_safe = strip_tags($title);
$content_safe = strip_tags($content);

try {
    $db->beginTransaction();
    $stmt = $db->prepare('UPDATE news SET title = :title, content = :content WHERE id = :id');
    $stmt->execute([
        ':title' => $title_safe,
        ':content' => $content_safe,
        ':id' => $id
    ]);

    $dryRun = finish_dry_run_transaction($db);
    echo json_encode(['success' => true, 'dryRun' => $dryRun]);
} catch (PDOException $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    generic_database_error('edit_news failed: ' . $e->getMessage());
}
