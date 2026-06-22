<?php

function maintenance_flag_path() {
    return __DIR__ . '/../MAINTENANCE';
}

function is_maintenance_enabled() {
    return file_exists(maintenance_flag_path());
}

function is_request_admin_allowed() {
    if (session_status() === PHP_SESSION_NONE) session_start();
    $allowed = false;
    if (isset($_SESSION['discord']) && !empty($GLOBALS['ALLOWED_DISCORD_IDS'])) {
        $allowed = in_array((string)($_SESSION['discord']['id'] ?? ''), $GLOBALS['ALLOWED_DISCORD_IDS'], true);
    }
    return $allowed;
}

function enforce_maintenance_json() {
    if (is_maintenance_enabled() && !is_request_admin_allowed()) {
        header('Content-Type: application/json; charset=utf-8');
        http_response_code(503);
        echo json_encode(['error' => 'Site is under maintenance. Please try again later.']);
        exit;
    }
}

function enforce_maintenance_html() {
    if (is_maintenance_enabled() && !is_request_admin_allowed()) {
        http_response_code(503);
        ?><!doctype html>
        <html><head><meta charset="utf-8"><title>Maintenance</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>body{font-family:Arial,Helvetica,sans-serif;background:#f4f4f9;color:#222;display:flex;align-items:center;justify-content:center;height:100vh;margin:0} .card{background:#fff;padding:28px;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,0.08);max-width:760px;text-align:center} h1{margin:0 0 8px 0;color:#123} p{color:#555} .meta{margin-top:12px;font-size:13px;color:#777} img{max-width:100%;height:auto;margin:20px 0;border-radius:8px;}</style>
        </head><body><div class="card"><h1>We'll be back soon</h1><img src="/img/maintenanceon.png" alt="Maintenance" style="max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px;"><p>Our site is temporarily under maintenance. We're working on improvements! Please check back later.</p><div class="meta">If you are an admin, please <a href="https://auth.hcr2.xyz/login">log in</a> to manage maintenance.</div></div></body></html><?php
        exit;
    }
}

?>