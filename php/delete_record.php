<?php
require_once __DIR__ . '/auth/check_auth.php';
ensure_authorized_json();

try {
    $db = get_database_connection();
} catch (PDOException $e) {
    generic_database_error('delete_record connection failed: ' . $e->getMessage());
}

$data = json_decode(file_get_contents('php://input'), true);

$recordId = $data['recordId'];

try {
    
    $stmt = $db->prepare("DELETE FROM _worldrecord WHERE idRecord = :recordId");
    $stmt->execute([':recordId' => $recordId]);

    echo json_encode(['success' => true]);
} catch (PDOException $e) {
    generic_database_error('delete_record failed: ' . $e->getMessage());
}
?>
