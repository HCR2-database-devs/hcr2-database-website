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
    $items = preg_split('/[\n,]+/', $value);
    return array_values(array_filter(array_map('trim', $items), fn($item) => $item !== ''));
}

load_dotenv(__DIR__ . '/../.env');

define('AUTH_SHARED_SECRET', env('AUTH_SHARED_SECRET'));
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
