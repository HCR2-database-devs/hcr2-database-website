BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'legacy' AND table_name = '_news_archived')
       AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = '_news') THEN
        EXECUTE format('CREATE TABLE %I._news AS TABLE legacy._news_archived', current_schema());
        DROP TABLE legacy._news_archived;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'legacy' AND table_name = '_pendingsubmission_archived')
       AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = '_pendingsubmission') THEN
        EXECUTE format('CREATE TABLE %I._pendingsubmission AS TABLE legacy._pendingsubmission_archived', current_schema());
        DROP TABLE legacy._pendingsubmission_archived;
    END IF;
END $$;

DROP INDEX IF EXISTS _worldrecord_current_map_vehicle_unique;
DROP INDEX IF EXISTS _tuningpart_nametuningpart_unique;
DROP INDEX IF EXISTS _player_nameplayer_unique;
DROP INDEX IF EXISTS _vehicle_namevehicle_unique;
DROP INDEX IF EXISTS _map_namemap_unique;

ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_tuningsetup_fk;
ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_player_fk;
ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_vehicle_fk;
ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_map_fk;
ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_questionable_check;
ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_current_check;
ALTER TABLE IF EXISTS _tuningsetupparts DROP CONSTRAINT IF EXISTS _tuningsetupparts_part_fk;
ALTER TABLE IF EXISTS _tuningsetupparts DROP CONSTRAINT IF EXISTS _tuningsetupparts_setup_fk;

ALTER TABLE IF EXISTS _worldrecord DROP CONSTRAINT IF EXISTS _worldrecord_pkey;
ALTER TABLE IF EXISTS _tuningsetupparts DROP CONSTRAINT IF EXISTS _tuningsetupparts_pkey;
ALTER TABLE IF EXISTS _tuningsetup DROP CONSTRAINT IF EXISTS _tuningsetup_pkey;
ALTER TABLE IF EXISTS _tuningpart DROP CONSTRAINT IF EXISTS _tuningpart_pkey;
ALTER TABLE IF EXISTS _player DROP CONSTRAINT IF EXISTS _player_pkey;
ALTER TABLE IF EXISTS _vehicle DROP CONSTRAINT IF EXISTS _vehicle_pkey;
ALTER TABLE IF EXISTS _map DROP CONSTRAINT IF EXISTS _map_pkey;

ALTER TABLE IF EXISTS _worldrecord ALTER COLUMN "idRecord" DROP DEFAULT;
ALTER TABLE IF EXISTS _worldrecord DROP COLUMN IF EXISTS "idRecord";
DROP SEQUENCE IF EXISTS _worldrecord_idrecord_seq;

ALTER TABLE IF EXISTS _worldrecord ALTER COLUMN "idTuningSetup" TYPE character varying(3) USING "idTuningSetup"::character varying;
ALTER TABLE IF EXISTS _worldrecord ALTER COLUMN current DROP DEFAULT;
ALTER TABLE IF EXISTS _worldrecord ALTER COLUMN questionable DROP DEFAULT;

ALTER TABLE IF EXISTS _map ALTER COLUMN "idMap" DROP DEFAULT;
ALTER TABLE IF EXISTS _vehicle ALTER COLUMN "idVehicle" DROP DEFAULT;
ALTER TABLE IF EXISTS _player ALTER COLUMN "idPlayer" DROP DEFAULT;
ALTER TABLE IF EXISTS _tuningpart ALTER COLUMN "idTuningPart" DROP DEFAULT;
ALTER TABLE IF EXISTS _tuningsetup ALTER COLUMN "idTuningSetup" DROP DEFAULT;

DROP SEQUENCE IF EXISTS _map_idmap_seq;
DROP SEQUENCE IF EXISTS _vehicle_idvehicle_seq;
DROP SEQUENCE IF EXISTS _player_idplayer_seq;
DROP SEQUENCE IF EXISTS _tuningpart_idtuningpart_seq;
DROP SEQUENCE IF EXISTS _tuningsetup_idtuningsetup_seq;

REVOKE USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public FROM hcr2user;

COMMIT;
