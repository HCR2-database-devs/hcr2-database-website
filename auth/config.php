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

function configure_session_cookie_settings(): void {
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }

    ini_set('session.cookie_secure', '1');
    ini_set('session.cookie_httponly', '1');
    ini_set('session.cookie_samesite', 'Lax');
}

configure_session_cookie_settings();

load_dotenv(__DIR__ . '/../.env');

function require_env(string $name): string {
    $value = env($name);
    if ($value === null || $value === '') {
        error_log("Missing required environment variable: $name");
        throw new RuntimeException("Configuration error: $name is not set");
    }
    return $value;
}

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

function generic_database_error(string $context = ''): void {
    if ($context !== '') {
        error_log('[DB] ' . $context);
    }
    safe_json_error('Database error', 500);
}

function api_dry_run_enabled(): bool {
    $value = strtolower((string)env('API_DRY_RUN', ''));
    return in_array($value, ['1', 'true', 'yes', 'on'], true);
}

function finish_dry_run_transaction(PDO $pdo): bool {
    if (api_dry_run_enabled() && $pdo->inTransaction()) {
        $pdo->rollBack();
        return true;
    }

    if ($pdo->inTransaction()) {
        $pdo->commit();
    }

    return false;
}

function db_column_exists(PDO $pdo, string $table, string $column): bool {
    static $cache = [];
    $key = $table . '.' . $column;
    if (array_key_exists($key, $cache)) {
        return $cache[$key];
    }

    $stmt = $pdo->prepare("
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = :table
          AND column_name = :column
        LIMIT 1
    ");
    $stmt->execute([':table' => $table, ':column' => $column]);
    return $cache[$key] = (bool)$stmt->fetchColumn();
}

function db_column_has_default(PDO $pdo, string $table, string $column): bool {
    static $cache = [];
    $key = $table . '.' . $column;
    if (array_key_exists($key, $cache)) {
        return $cache[$key];
    }

    $stmt = $pdo->prepare("
        SELECT column_default
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = :table
          AND column_name = :column
        LIMIT 1
    ");
    $stmt->execute([':table' => $table, ':column' => $column]);
    $default = $stmt->fetchColumn();
    return $cache[$key] = is_string($default) && $default !== '';
}

function next_legacy_id(PDO $pdo, string $table, string $column): int {
    $quotedColumn = '"' . str_replace('"', '""', $column) . '"';
    $stmt = $pdo->query("SELECT COALESCE(MAX($quotedColumn), 0) + 1 AS next_id FROM $table");
    return (int)$stmt->fetchColumn();
}

function worldrecord_has_id_record(PDO $pdo): bool {
    return db_column_exists($pdo, '_worldrecord', 'idRecord');
}

function record_key_sql(string $alias = 'wr'): string {
    $pdo = get_database_connection();
    if (worldrecord_has_id_record($pdo)) {
        return $alias . '."idRecord"::text';
    }

    return $alias . '."idMap"::text || \':\' || ' . $alias . '."idVehicle"::text';
}

function record_key_where_sql(string $alias = ''): string {
    $pdo = get_database_connection();
    $prefix = $alias !== '' ? $alias . '.' : '';
    if (worldrecord_has_id_record($pdo)) {
        return $prefix . '"idRecord" = :idRecord';
    }

    return $prefix . '"idMap" = :idMap AND ' . $prefix . '"idVehicle" = :idVehicle';
}

function parse_record_key($recordId): ?array {
    if (!is_string($recordId) && !is_int($recordId)) {
        return null;
    }

    $recordId = trim((string)$recordId);
    if (preg_match('/^\d+$/', $recordId)) {
        return ['idRecord' => (int)$recordId];
    }

    if (preg_match('/^(\d+):(\d+)$/', $recordId, $matches)) {
        return [
            'idMap' => (int)$matches[1],
            'idVehicle' => (int)$matches[2],
        ];
    }

    return null;
}

function record_key_params(array $recordKey): array {
    if (isset($recordKey['idRecord'])) {
        return [':idRecord' => $recordKey['idRecord']];
    }

    return [
        ':idMap' => $recordKey['idMap'],
        ':idVehicle' => $recordKey['idVehicle'],
    ];
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
    $config = [
        'host' => env('DB_HOST') ?: env('PGHOST') ?: env('POSTGRES_HOST'),
        'port' => env('DB_PORT') ?: env('PGPORT') ?: env('POSTGRES_PORT') ?: '5432',
        'dbname' => env('DB_NAME') ?: env('PGDATABASE') ?: env('POSTGRES_DB'),
        'user' => env('DB_USER') ?: env('PGUSER') ?: env('POSTGRES_USER'),
        'pass' => env('DB_PASS') ?: env('PGPASSWORD') ?: env('POSTGRES_PASSWORD'),
    ];

    $databaseUrl = env('DATABASE_URL') ?: env('POSTGRES_URL') ?: env('POSTGRESQL_URL');
    if ($databaseUrl) {
        $parts = parse_url($databaseUrl);
        if ($parts !== false) {
            $config['host'] = $config['host'] ?: ($parts['host'] ?? null);
            $config['port'] = $config['port'] ?: (isset($parts['port']) ? (string)$parts['port'] : null);
            $config['dbname'] = $config['dbname'] ?: (isset($parts['path']) ? ltrim($parts['path'], '/') : null);
            $config['user'] = $config['user'] ?: ($parts['user'] ?? null);
            $config['pass'] = $config['pass'] ?: ($parts['pass'] ?? null);

            if (!empty($parts['query'])) {
                parse_str($parts['query'], $query);
                $config['host'] = $config['host'] ?: ($query['host'] ?? null);
                $config['port'] = $config['port'] ?: ($query['port'] ?? null);
                $config['dbname'] = $config['dbname'] ?: ($query['dbname'] ?? null);
                $config['user'] = $config['user'] ?: ($query['user'] ?? null);
                $config['pass'] = $config['pass'] ?: ($query['password'] ?? null);
            }
        }
    }

    return $config;
}

function get_database_connection(): PDO {
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $config = get_database_config();
    foreach (['host', 'port', 'dbname', 'user'] as $key) {
        if ($config[$key] === null || $config[$key] === '') {
            throw new RuntimeException("Configuration error: database $key is not set");
        }
    }

    $dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s', $config['host'], $config['port'], $config['dbname']);
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];

    $pdo = new PDO($dsn, $config['user'], $config['pass'], $options);
    $schema = env('DB_SCHEMA') ?: env('PGSCHEMA');
    if ($schema !== null && $schema !== '') {
        if (!preg_match('/^[A-Za-z_][A-Za-z0-9_]*$/', $schema)) {
            throw new RuntimeException('Configuration error: invalid DB_SCHEMA');
        }
        $pdo->exec('SET search_path TO "' . str_replace('"', '""', $schema) . '", public');
    }
    return $pdo;
}

function resolve_pg_table(PDO $pdo, array $candidates): string {
    static $resolved = [];

    $cacheKey = implode('|', $candidates);
    if (isset($resolved[$cacheKey])) {
        return $resolved[$cacheKey];
    }

    $stmt = $pdo->prepare('SELECT to_regclass(:relation_name)');
    foreach ($candidates as $candidate) {
        $stmt->execute([':relation_name' => $candidate]);
        $relationName = $stmt->fetchColumn();
        if (is_string($relationName) && $relationName !== '') {
            return $resolved[$cacheKey] = $relationName;
        }
    }

    throw new RuntimeException('Required database table was not found');
}

function pending_submissions_table(PDO $pdo): string {
    if (db_column_exists($pdo, 'pendingsubmission', 'tuningparts')) {
        return 'pendingsubmission';
    }

    return resolve_pg_table($pdo, [
        '_pendingsubmission',
        'public._pendingsubmission',
        'pending_submission',
        'public.pending_submission',
        'pendingsubmission',
        'public.pendingsubmission',
    ]);
}
