<?php
function try_curl($url) {
    if (!function_exists('curl_init')) {
        echo "cURL not available\n";
        return;
    }
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
    $body = curl_exec($ch);
    $err = curl_error($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    echo "CURL code: $code\n";
    echo "CURL error: " . ($err ?: 'none') . "\n";
    echo "Body (first 1024 bytes):\n" . substr($body ?: '', 0, 1024) . "\n";
}

function try_file_get_contents($url) {
    echo "\nfile_get_contents test:\n";
    $ctx = stream_context_create([
        'http' => ['timeout' => 10],
        'ssl' => ['verify_peer' => true, 'verify_peer_name' => true]
    ]);
    $body = @file_get_contents($url, false, $ctx);
    if ($body === false) {
        echo "file_get_contents failed\n";
    } else {
        echo "file_get_contents ok, first 1024 bytes:\n" . substr($body, 0, 1024) . "\n";
    }
}

$url = 'https://discord.com/api/';
echo "Testing outbound to: $url\n\n";
try_curl($url);
try_file_get_contents($url);