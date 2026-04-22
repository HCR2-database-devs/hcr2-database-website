#!/usr/bin/env php
<?php
require_once __DIR__ . '/../auth/config.php';

header('Content-Type: text/plain; charset=utf-8');

function suspicious_score(string $value): int {
    $patterns = [
        '/\x{00C3}/u',
        '/\x{00C2}/u',
        '/\x{00E2}/u',
        '/\x{00F0}/u',
        '/\x{FFFD}/u',
    ];

    $score = 0;
    foreach ($patterns as $pattern) {
        $count = preg_match_all($pattern, $value);
        if ($count !== false) {
            $score += $count;
        }
    }

    return $score;
}

function repair_text(string $value): string {
    if ($value === '') {
        return $value;
    }

    $initial = suspicious_score($value);
    if ($initial === 0) {
        return $value;
    }

    $candidate = utf8_decode($value);
    if (!mb_check_encoding($candidate, 'UTF-8')) {
        return $value;
    }

    return suspicious_score($candidate) < $initial ? $candidate : $value;
}

function repair_table(PDO $db, string $table): int {
    $db->beginTransaction();

    $stmt = $db->query("SELECT ctid::text AS row_id, title, content, author FROM {$table}");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $updated = 0;
    $updateStmt = $db->prepare("UPDATE {$table} SET title = :title, content = :content, author = :author WHERE ctid::text = :row_id");

    foreach ($rows as $row) {
        $newTitle = isset($row['title']) ? repair_text((string)$row['title']) : '';
        $newContent = isset($row['content']) ? repair_text((string)$row['content']) : '';
        $newAuthor = isset($row['author']) ? repair_text((string)$row['author']) : '';

        if ($newTitle === $row['title'] && $newContent === $row['content'] && $newAuthor === $row['author']) {
            continue;
        }

        $updateStmt->execute([
            ':title' => $newTitle,
            ':content' => $newContent,
            ':author' => $newAuthor,
            ':row_id' => $row['row_id'],
        ]);
        $updated++;
    }

    $db->commit();
    return $updated;
}

try {
    $db = get_database_connection();

    $updatedNews = repair_table($db, 'news');
    echo "news: {$updatedNews} row(s) updated\n";

    $hasLegacy = (bool)$db->query("SELECT to_regclass('_news') IS NOT NULL")->fetchColumn();
    if ($hasLegacy) {
        $updatedLegacyNews = repair_table($db, '_news');
        echo "_news: {$updatedLegacyNews} row(s) updated\n";
    }

    echo "Done.\n";
} catch (Throwable $e) {
    fwrite(STDERR, 'Error: ' . $e->getMessage() . PHP_EOL);
    exit(1);
}
