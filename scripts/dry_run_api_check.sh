#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${DRY_RUN_HOST:-127.0.0.1}"
PORT="${DRY_RUN_PORT:-8765}"
BASE_URL="http://${HOST}:${PORT}"
TMP_DIR="$(mktemp -d)"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"

php -r '
require "auth/config.php";
$pdo = get_database_connection();
$checks = [
    ["_worldrecord", "idRecord"],
    ["pendingsubmission", "tuningparts"],
];
foreach ($checks as [$table, $column]) {
    $stmt = $pdo->prepare("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = :table AND column_name = :column");
    $stmt->execute([":table" => $table, ":column" => $column]);
    if (!$stmt->fetchColumn()) {
        fwrite(STDERR, "Normalized PostgreSQL schema is required before running dry_run_api_check.sh. Run scripts/rehearse_postgresql_migration.sh first, then apply the migration.\n");
        exit(2);
    }
}
'

API_DRY_RUN=1 php -S "${HOST}:${PORT}" -t "$ROOT_DIR" >"${TMP_DIR}/server.log" 2>&1 &
SERVER_PID="$!"
sleep 1

TOKEN="$(php -r '
require "auth/config.php";
$ids = $GLOBALS["ALLOWED_DISCORD_IDS"] ?? [];
$sub = $ids[0] ?? "dry-run-admin";
$payload = ["sub" => (string)$sub, "username" => "dryrun", "exp" => time() + 3600];
$h = rtrim(strtr(base64_encode(json_encode(["alg" => "HS256", "typ" => "JWT"])), "+/", "-_"), "=");
$p = rtrim(strtr(base64_encode(json_encode($payload)), "+/", "-_"), "=");
$s = rtrim(strtr(base64_encode(hash_hmac("sha256", "$h.$p", AUTH_SHARED_SECRET, true)), "+/", "-_"), "=");
echo "$h.$p.$s";
')"

API_KEY="$(php -r 'require "auth/config.php"; echo (($GLOBALS["API_KEYS"] ?? [])[0] ?? "");')"
EMPTY_SETUP_RECORD="$(php -r '
require "auth/config.php";
$pdo = get_database_connection();
$sql = "SELECT " . record_key_sql("wr") . " AS id FROM _worldrecord wr WHERE wr.current = 1 AND (wr.\"idTuningSetup\" IS NULL OR wr.\"idTuningSetup\" = 0) LIMIT 1";
$row = $pdo->query($sql)->fetch(PDO::FETCH_ASSOC);
echo $row["id"] ?? "1";
')"

CURRENT_RECORD="$(php -r '
require "auth/config.php";
$pdo = get_database_connection();
$row = $pdo->query("SELECT " . record_key_sql("wr") . " AS id FROM _worldrecord wr WHERE wr.current = 1 ORDER BY wr.\"idRecord\" LIMIT 1")->fetch(PDO::FETCH_ASSOC);
echo $row["id"] ?? "1";
')"

request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local label="${method} ${path}"
  local out="${TMP_DIR}/response.txt"

  if [[ "$method" == "GET" ]]; then
    curl -sS -o "$out" -w "%{http_code}" -H "Cookie: WC_TOKEN=${TOKEN}" "${BASE_URL}${path}" >"${TMP_DIR}/status.txt"
  else
    curl -sS -o "$out" -w "%{http_code}" -H "Cookie: WC_TOKEN=${TOKEN}" -H "Content-Type: application/json" -d "$body" "${BASE_URL}${path}" >"${TMP_DIR}/status.txt"
  fi

  local status
  status="$(cat "${TMP_DIR}/status.txt")"
  if [[ "$status" =~ ^5 ]]; then
    echo "FAIL ${label} -> HTTP ${status}"
    cat "$out"
    echo
    return 1
  fi
  echo "OK   ${label} -> HTTP ${status}"
}

request GET "/php/load_data.php?type=maps"
request GET "/php/load_data.php?type=vehicles"
request GET "/php/load_data.php?type=players"
request GET "/php/load_data.php?type=tuning_parts"
request GET "/php/load_data.php?type=tuning_setups"
request GET "/php/load_data.php?type=records"
request GET "/php/get_news.php?limit=5"
request GET "/php/maintenance_status.php"
request GET "/php/get_hcaptcha_sitekey.php"
request GET "/auth/status.php"
request GET "/auth/admin_pending.php"
request GET "/auth/admin_actions.php"

if [[ -n "$API_KEY" ]]; then
  request GET "/php/api_records.php?api_key=${API_KEY}&limit=2"
fi

request POST "/php/add_map.php" '{"mapName":"DryRunMap"}'
request POST "/php/add_vehicle.php" '{"vehicleName":"DryRunVehicle"}'
request POST "/php/add_tuning_part.php" '{"partName":"DryRunPart"}'
request POST "/php/add_tuning_setup.php" '{"partIds":[1,2,3]}'
request POST "/php/submit_record.php" '{"mapId":1,"vehicleId":1,"distance":12345,"playerId":1,"tuningSetupId":1,"questionable":0}'
request POST "/php/set_questionable.php" "{\"recordId\":\"${CURRENT_RECORD}\",\"questionable\":1,\"note\":\"dry run\"}"
request POST "/php/assign_setup.php" "{\"recordId\":\"${EMPTY_SETUP_RECORD}\",\"tuningSetupId\":1}"
request POST "/php/delete_record.php" "{\"recordId\":\"${CURRENT_RECORD}\"}"
request POST "/php/public_submit.php" '{"h_captcha_response":"dry","mapId":1,"vehicleId":1,"distance":12345,"playerName":"DryRunner","playerCountry":"Nowhere","tuningParts":["Wings","Nitro","Magnet"],"form_load_time":1,"submission_time":4000}'
request POST "/auth/post_news.php" '{"title":"Dry run title","content":"Dry run content"}'
request POST "/php/set_maintenance.php" '{"action":"enable"}'

if grep -Ei "fatal|warning|database error|undefined|exception" "${TMP_DIR}/server.log" >/dev/null; then
  echo "Server log contains suspicious entries:"
  grep -Ei "fatal|warning|database error|undefined|exception" "${TMP_DIR}/server.log"
  exit 1
fi

echo "Dry-run API check completed."
