BEGIN;

DROP TABLE IF EXISTS _sqlite_sequence;

DO $$
BEGIN
    IF to_regclass('public._map') IS NOT NULL THEN
        ALTER TABLE _map RENAME TO map;
    END IF;
    IF to_regclass('public._vehicle') IS NOT NULL THEN
        ALTER TABLE _vehicle RENAME TO vehicle;
    END IF;
    IF to_regclass('public._player') IS NOT NULL THEN
        ALTER TABLE _player RENAME TO player;
    END IF;
    IF to_regclass('public._tuningpart') IS NOT NULL THEN
        ALTER TABLE _tuningpart RENAME TO tuning_part;
    END IF;
    IF to_regclass('public._tuningsetup') IS NOT NULL THEN
        ALTER TABLE _tuningsetup RENAME TO tuning_setup;
    END IF;
    IF to_regclass('public._tuningsetupparts') IS NOT NULL THEN
        ALTER TABLE _tuningsetupparts RENAME TO tuning_setup_part;
    END IF;
    IF to_regclass('public._worldrecord') IS NOT NULL THEN
        ALTER TABLE _worldrecord RENAME TO world_record;
    END IF;
    IF to_regclass('public.pendingsubmission') IS NOT NULL THEN
        ALTER TABLE pendingsubmission RENAME TO pending_submission;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='map' AND column_name='idMap') THEN
        ALTER TABLE map RENAME COLUMN "idMap" TO id_map;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='map' AND column_name='nameMap') THEN
        ALTER TABLE map RENAME COLUMN "nameMap" TO name_map;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='vehicle' AND column_name='idVehicle') THEN
        ALTER TABLE vehicle RENAME COLUMN "idVehicle" TO id_vehicle;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='vehicle' AND column_name='nameVehicle') THEN
        ALTER TABLE vehicle RENAME COLUMN "nameVehicle" TO name_vehicle;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='player' AND column_name='idPlayer') THEN
        ALTER TABLE player RENAME COLUMN "idPlayer" TO id_player;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='player' AND column_name='namePlayer') THEN
        ALTER TABLE player RENAME COLUMN "namePlayer" TO name_player;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='tuning_part' AND column_name='idTuningPart') THEN
        ALTER TABLE tuning_part RENAME COLUMN "idTuningPart" TO id_tuning_part;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='tuning_part' AND column_name='nameTuningPart') THEN
        ALTER TABLE tuning_part RENAME COLUMN "nameTuningPart" TO name_tuning_part;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='tuning_setup' AND column_name='idTuningSetup') THEN
        ALTER TABLE tuning_setup RENAME COLUMN "idTuningSetup" TO id_tuning_setup;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='tuning_setup_part' AND column_name='idTuningSetup') THEN
        ALTER TABLE tuning_setup_part RENAME COLUMN "idTuningSetup" TO id_tuning_setup;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='tuning_setup_part' AND column_name='idTuningPart') THEN
        ALTER TABLE tuning_setup_part RENAME COLUMN "idTuningPart" TO id_tuning_part;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='world_record' AND column_name='idMap') THEN
        ALTER TABLE world_record RENAME COLUMN "idMap" TO id_map;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='world_record' AND column_name='idVehicle') THEN
        ALTER TABLE world_record RENAME COLUMN "idVehicle" TO id_vehicle;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='world_record' AND column_name='idPlayer') THEN
        ALTER TABLE world_record RENAME COLUMN "idPlayer" TO id_player;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='world_record' AND column_name='idTuningSetup') THEN
        ALTER TABLE world_record RENAME COLUMN "idTuningSetup" TO id_tuning_setup;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='world_record' AND column_name='idRecord') THEN
        ALTER TABLE world_record RENAME COLUMN "idRecord" TO id_record;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='idmap') THEN
        ALTER TABLE pending_submission RENAME COLUMN idmap TO id_map;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='idvehicle') THEN
        ALTER TABLE pending_submission RENAME COLUMN idvehicle TO id_vehicle;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='playername') THEN
        ALTER TABLE pending_submission RENAME COLUMN playername TO player_name;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='playercountry') THEN
        ALTER TABLE pending_submission RENAME COLUMN playercountry TO player_country;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='submitterip') THEN
        ALTER TABLE pending_submission RENAME COLUMN submitterip TO submitter_ip;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='pending_submission' AND column_name='tuningparts') THEN
        ALTER TABLE pending_submission RENAME COLUMN tuningparts TO tuning_parts;
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public._map_idmap_seq') IS NOT NULL THEN
        ALTER SEQUENCE _map_idmap_seq RENAME TO map_id_seq;
    END IF;
    IF to_regclass('public._vehicle_idvehicle_seq') IS NOT NULL THEN
        ALTER SEQUENCE _vehicle_idvehicle_seq RENAME TO vehicle_id_seq;
    END IF;
    IF to_regclass('public._player_idplayer_seq') IS NOT NULL THEN
        ALTER SEQUENCE _player_idplayer_seq RENAME TO player_id_seq;
    END IF;
    IF to_regclass('public._tuningpart_idtuningpart_seq') IS NOT NULL THEN
        ALTER SEQUENCE _tuningpart_idtuningpart_seq RENAME TO tuning_part_id_seq;
    END IF;
    IF to_regclass('public._tuningsetup_idtuningsetup_seq') IS NOT NULL THEN
        ALTER SEQUENCE _tuningsetup_idtuningsetup_seq RENAME TO tuning_setup_id_seq;
    END IF;
    IF to_regclass('public._worldrecord_idrecord_seq') IS NOT NULL THEN
        ALTER SEQUENCE _worldrecord_idrecord_seq RENAME TO world_record_id_seq;
    END IF;
    IF to_regclass('public.pendingsubmission_id_seq') IS NOT NULL THEN
        ALTER SEQUENCE pendingsubmission_id_seq RENAME TO pending_submission_id_seq;
    END IF;
END $$;

ALTER TABLE map ALTER COLUMN id_map SET DEFAULT nextval('map_id_seq');
ALTER TABLE vehicle ALTER COLUMN id_vehicle SET DEFAULT nextval('vehicle_id_seq');
ALTER TABLE player ALTER COLUMN id_player SET DEFAULT nextval('player_id_seq');
ALTER TABLE tuning_part ALTER COLUMN id_tuning_part SET DEFAULT nextval('tuning_part_id_seq');
ALTER TABLE tuning_setup ALTER COLUMN id_tuning_setup SET DEFAULT nextval('tuning_setup_id_seq');
ALTER TABLE world_record ALTER COLUMN id_record SET DEFAULT nextval('world_record_id_seq');
ALTER TABLE pending_submission ALTER COLUMN id SET DEFAULT nextval('pending_submission_id_seq');

ALTER SEQUENCE map_id_seq OWNED BY map.id_map;
ALTER SEQUENCE vehicle_id_seq OWNED BY vehicle.id_vehicle;
ALTER SEQUENCE player_id_seq OWNED BY player.id_player;
ALTER SEQUENCE tuning_part_id_seq OWNED BY tuning_part.id_tuning_part;
ALTER SEQUENCE tuning_setup_id_seq OWNED BY tuning_setup.id_tuning_setup;
ALTER SEQUENCE world_record_id_seq OWNED BY world_record.id_record;
ALTER SEQUENCE pending_submission_id_seq OWNED BY pending_submission.id;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_map_pkey') THEN
        ALTER TABLE map RENAME CONSTRAINT _map_pkey TO map_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_vehicle_pkey') THEN
        ALTER TABLE vehicle RENAME CONSTRAINT _vehicle_pkey TO vehicle_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_player_pkey') THEN
        ALTER TABLE player RENAME CONSTRAINT _player_pkey TO player_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningpart_pkey') THEN
        ALTER TABLE tuning_part RENAME CONSTRAINT _tuningpart_pkey TO tuning_part_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetup_pkey') THEN
        ALTER TABLE tuning_setup RENAME CONSTRAINT _tuningsetup_pkey TO tuning_setup_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_pkey') THEN
        ALTER TABLE tuning_setup_part RENAME CONSTRAINT _tuningsetupparts_pkey TO tuning_setup_part_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_pkey') THEN
        ALTER TABLE world_record RENAME CONSTRAINT _worldrecord_pkey TO world_record_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_map_fk') THEN
        ALTER TABLE world_record RENAME CONSTRAINT _worldrecord_map_fk TO world_record_map_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_vehicle_fk') THEN
        ALTER TABLE world_record RENAME CONSTRAINT _worldrecord_vehicle_fk TO world_record_vehicle_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_player_fk') THEN
        ALTER TABLE world_record RENAME CONSTRAINT _worldrecord_player_fk TO world_record_player_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_tuningsetup_fk') THEN
        ALTER TABLE world_record RENAME CONSTRAINT _worldrecord_tuningsetup_fk TO world_record_tuning_setup_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_setup_fk') THEN
        ALTER TABLE tuning_setup_part RENAME CONSTRAINT _tuningsetupparts_setup_fk TO tuning_setup_part_setup_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_part_fk') THEN
        ALTER TABLE tuning_setup_part RENAME CONSTRAINT _tuningsetupparts_part_fk TO tuning_setup_part_part_fk;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pendingsubmission_pkey') THEN
        ALTER TABLE pending_submission RENAME CONSTRAINT pendingsubmission_pkey TO pending_submission_pkey;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pendingsubmission_status_check') THEN
        ALTER TABLE pending_submission RENAME CONSTRAINT pendingsubmission_status_check TO pending_submission_status_check;
    END IF;
END $$;

ALTER INDEX IF EXISTS _worldrecord_current_map_vehicle_unique RENAME TO world_record_current_map_vehicle_unique;
ALTER INDEX IF EXISTS pendingsubmission_status_submitted_idx RENAME TO pending_submission_status_submitted_idx;
ALTER INDEX IF EXISTS pendingsubmission_map_vehicle_idx RENAME TO pending_submission_map_vehicle_idx;

GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO hcr2user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO hcr2user;

COMMIT;
