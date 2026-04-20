<?php
require_once __DIR__ . '/php/maintenance_helpers.php';
enforce_maintenance_html();

$html = __DIR__ . '/index.html';
if (file_exists($html)) {
    header('Content-Type: text/html; charset=utf-8');
    readfile($html);
    exit;
}

echo "<html><body><h1>Index not found</h1></body></html>";
?>
