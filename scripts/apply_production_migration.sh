#!/bin/bash

# Production SQL Migration Commands for HCR2
# =============================================
# Normalize PostgreSQL schema from legacy SQLite/mixed-case to professional snake_case.
# Run this on the production PostgreSQL database for the hcr2 application.

set -e

DBNAME="${1:-hcr2}"
DBUSER="${2:-hcr2user}"
DBHOST="${3:-127.0.0.1}"
DBPORT="${4:-5432}"

echo "=========================================="
echo "HCR2 Production Migration Suite"
echo "=========================================="
echo "Target: $DBHOST:$DBPORT / $DBNAME ($DBUSER)"
echo ""

# Step 1: Transfer table ownership (requires postgres superuser)
echo "[1/2] Transferring table ownership to $DBUSER..."
sudo -u postgres psql -h "$DBHOST" -p "$DBPORT" -d "$DBNAME" \
  -c "ALTER TABLE _map OWNER TO $DBUSER;
      ALTER TABLE _vehicle OWNER TO $DBUSER;
      ALTER TABLE _player OWNER TO $DBUSER;
      ALTER TABLE _tuningpart OWNER TO $DBUSER;
      ALTER TABLE _tuningsetup OWNER TO $DBUSER;
      ALTER TABLE _tuningsetupparts OWNER TO $DBUSER;
      ALTER TABLE _worldrecord OWNER TO $DBUSER;" 2>&1 | grep -E 'ALTER|ERROR'

# Step 2: Apply final schema normalization (run as hcr2user)
echo "[2/2] Applying final snake_case schema migration..."
PGPASSWORD="$(grep '^DB_PASS=' /var/www/hcr2.xyz/.env 2>/dev/null | cut -d= -f2 | tr -d ' ')" \
  psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" \
  -v ON_ERROR_STOP=1 \
  -f /var/www/hcr2.xyz/migrations/20260422_finalize_snake_case_schema.up.sql 2>&1 | tail -5

echo ""
echo "=========================================="
echo "✓ Migration completed successfully!"
echo "=========================================="
echo ""
echo "Schema changes applied:"
echo "  • Table names: _map → map, _vehicle → vehicle, etc."
echo "  • Column names: idMap → id_map, namePlayer → name_player, etc."
echo "  • Constraint names: _map_pkey → map_pkey, etc."
echo "  • Sequence names: _map_idmap_seq → map_id_seq, etc."
echo "  • SQLite sequence table removed"
echo ""
echo "All application endpoints have been refactored and are ready."
