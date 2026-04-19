<?php

function load_dotenv(string $path): void {
    if (!is_file($path)) {
        return;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) {
            continue;
        }

        if (!preg_match('/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/', $line, $matches)) {
            continue;
        }

        $name = $matches[1];
        $value = $matches[2];

        if ((str_starts_with($value, '"') && str_ends_with($value, '"')) || (str_starts_with($value, "'") && str_ends_with($value, "'"))) {
            $value = substr($value, 1, -1);
        }

        $value = str_replace(['\\n', '\\r', '\\t'], ["\n", "\r", "\t"], $value);

        if (getenv($name) === false) {
            putenv("$name=$value");
            $_ENV[$name] = $value;
            $_SERVER[$name] = $value;
        }
    }
}

function env(string $name, $default = null) {
    $value = getenv($name);
    return $value === false ? $default : $value;
}

function env_list(string $value): array {
    $items = preg_split('/[\n,]+/', (string)$value);
    return array_values(array_filter(array_map('trim', $items), fn($item) => $item !== ''));
}

ini_set('display_errors', '0');
ini_set('display_startup_errors', '0');
ini_set('session.cookie_secure', '1');
ini_set('session.cookie_httponly', '1');
ini_set('session.cookie_samesite', 'Lax');

load_dotenv(__DIR__ . '/../.env');

function require_env(string $name): string {
    $value = env($name);
    if ($value === null || $value === '') {
        error_log("Missing required environment variable: $name");
        throw new RuntimeException("Configuration error: $name is not set");
    }
    return $value;
}

function safe_json_error(string $message, int $statusCode = 500): void {
    if (!headers_sent()) {
        header('Content-Type: application/json; charset=utf-8');
        http_response_code($statusCode);
    }
    echo json_encode(['error' => $message]);
    exit;
}

function generic_database_error(string $context = ''): void {
    if ($context !== '') {
        error_log('[DB] ' . $context);
    }
    safe_json_error('Database error', 500);
}

function send_security_headers(): void {
    if (headers_sent()) {
        return;
    }
    header('X-Frame-Options: DENY');
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: same-origin');
    header('X-XSS-Protection: 1; mode=block');
    header('Permissions-Policy: geolocation=(), microphone=(), camera=()');
}

send_security_headers();

define('AUTH_SHARED_SECRET', require_env('AUTH_SHARED_SECRET'));
$ALLOWED_DISCORD_IDS = env_list(env('ALLOWED_DISCORD_IDS'));
$API_KEYS = env_list(env('API_KEYS'));
define('HCAPTCHA_SITE_KEY', env('HCAPTCHA_SITE_KEY'));
define('HCAPTCHA_SECRET_KEY', env('HCAPTCHA_SECRET_KEY'));

function get_database_config(): array {
    return [
        'host' => env('DB_HOST'),
        'port' => env('DB_PORT'),
        'dbname' => env('DB_NAME'),
        'user' => env('DB_USER'),
        'pass' => env('DB_PASS'),
    ];
}

function get_database_connection(): PDO {
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $config = get_database_config();
    $dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s', $config['host'], $config['port'], $config['dbname']);
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];

    $pdo = new PDO($dsn, $config['user'], $config['pass'], $options);
    return $pdo;
}
