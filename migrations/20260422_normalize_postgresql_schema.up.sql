BEGIN;

CREATE SCHEMA IF NOT EXISTS legacy;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM _map GROUP BY "idMap" HAVING count(*) > 1) THEN RAISE EXCEPTION '_map has duplicate idMap values'; END IF;
    IF EXISTS (SELECT 1 FROM _vehicle GROUP BY "idVehicle" HAVING count(*) > 1) THEN RAISE EXCEPTION '_vehicle has duplicate idVehicle values'; END IF;
    IF EXISTS (SELECT 1 FROM _player GROUP BY "idPlayer" HAVING count(*) > 1) THEN RAISE EXCEPTION '_player has duplicate idPlayer values'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningpart GROUP BY "idTuningPart" HAVING count(*) > 1) THEN RAISE EXCEPTION '_tuningpart has duplicate idTuningPart values'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningsetup GROUP BY "idTuningSetup" HAVING count(*) > 1) THEN RAISE EXCEPTION '_tuningsetup has duplicate idTuningSetup values'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningsetupparts GROUP BY "idTuningSetup", "idTuningPart" HAVING count(*) > 1) THEN RAISE EXCEPTION '_tuningsetupparts has duplicate setup/part pairs'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord WHERE current = 1 GROUP BY "idMap", "idVehicle" HAVING count(*) > 1) THEN RAISE EXCEPTION '_worldrecord has duplicate current map/vehicle records'; END IF;
    IF EXISTS (SELECT 1 FROM _map WHERE "idMap" IS NULL OR "nameMap" IS NULL OR "nameMap" = '') THEN RAISE EXCEPTION '_map has null required values'; END IF;
    IF EXISTS (SELECT 1 FROM _vehicle WHERE "idVehicle" IS NULL OR "nameVehicle" IS NULL OR "nameVehicle" = '') THEN RAISE EXCEPTION '_vehicle has null required values'; END IF;
    IF EXISTS (SELECT 1 FROM _player WHERE "idPlayer" IS NULL OR "namePlayer" IS NULL OR "namePlayer" = '') THEN RAISE EXCEPTION '_player has null required values'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningpart WHERE "idTuningPart" IS NULL OR "nameTuningPart" IS NULL OR "nameTuningPart" = '') THEN RAISE EXCEPTION '_tuningpart has null required values'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningsetup WHERE "idTuningSetup" IS NULL) THEN RAISE EXCEPTION '_tuningsetup has null idTuningSetup values'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord WHERE "idMap" IS NULL OR "idVehicle" IS NULL OR "idPlayer" IS NULL OR distance IS NULL OR current IS NULL) THEN RAISE EXCEPTION '_worldrecord has null required values'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord WHERE current NOT IN (0, 1) OR (questionable IS NOT NULL AND questionable NOT IN (0, 1))) THEN RAISE EXCEPTION '_worldrecord has invalid boolean-like values'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord wr LEFT JOIN _map m ON wr."idMap" = m."idMap" WHERE m."idMap" IS NULL) THEN RAISE EXCEPTION '_worldrecord has orphan map references'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord wr LEFT JOIN _vehicle v ON wr."idVehicle" = v."idVehicle" WHERE v."idVehicle" IS NULL) THEN RAISE EXCEPTION '_worldrecord has orphan vehicle references'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord wr LEFT JOIN _player p ON wr."idPlayer" = p."idPlayer" WHERE p."idPlayer" IS NULL) THEN RAISE EXCEPTION '_worldrecord has orphan player references'; END IF;
    IF EXISTS (SELECT 1 FROM _worldrecord wr LEFT JOIN _tuningsetup ts ON NULLIF(wr."idTuningSetup", '')::integer = ts."idTuningSetup" WHERE NULLIF(wr."idTuningSetup", '') IS NOT NULL AND ts."idTuningSetup" IS NULL) THEN RAISE EXCEPTION '_worldrecord has orphan tuning setup references'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningsetupparts tsp LEFT JOIN _tuningsetup ts ON tsp."idTuningSetup" = ts."idTuningSetup" WHERE ts."idTuningSetup" IS NULL) THEN RAISE EXCEPTION '_tuningsetupparts has orphan setup references'; END IF;
    IF EXISTS (SELECT 1 FROM _tuningsetupparts tsp LEFT JOIN _tuningpart tp ON tsp."idTuningPart" = tp."idTuningPart" WHERE tp."idTuningPart" IS NULL) THEN RAISE EXCEPTION '_tuningsetupparts has orphan part references'; END IF;
END $$;

CREATE SEQUENCE IF NOT EXISTS _map_idmap_seq;
ALTER TABLE _map ALTER COLUMN "idMap" TYPE integer;
ALTER TABLE _map ALTER COLUMN "idMap" SET NOT NULL;
ALTER TABLE _map ALTER COLUMN "idMap" SET DEFAULT nextval('_map_idmap_seq');
ALTER TABLE _map ALTER COLUMN "nameMap" SET NOT NULL;
ALTER TABLE _map ALTER COLUMN special SET DEFAULT 0;
UPDATE _map SET special = 0 WHERE special IS NULL;
ALTER TABLE _map ALTER COLUMN special SET NOT NULL;
ALTER SEQUENCE _map_idmap_seq OWNED BY _map."idMap";
SELECT setval('_map_idmap_seq', GREATEST((SELECT COALESCE(MAX("idMap"), 0) FROM _map), 1), true);

CREATE SEQUENCE IF NOT EXISTS _vehicle_idvehicle_seq;
ALTER TABLE _vehicle ALTER COLUMN "idVehicle" TYPE integer;
ALTER TABLE _vehicle ALTER COLUMN "idVehicle" SET NOT NULL;
ALTER TABLE _vehicle ALTER COLUMN "idVehicle" SET DEFAULT nextval('_vehicle_idvehicle_seq');
ALTER TABLE _vehicle ALTER COLUMN "nameVehicle" SET NOT NULL;
ALTER SEQUENCE _vehicle_idvehicle_seq OWNED BY _vehicle."idVehicle";
SELECT setval('_vehicle_idvehicle_seq', GREATEST((SELECT COALESCE(MAX("idVehicle"), 0) FROM _vehicle), 1), true);

CREATE SEQUENCE IF NOT EXISTS _player_idplayer_seq;
ALTER TABLE _player ALTER COLUMN "idPlayer" TYPE integer;
ALTER TABLE _player ALTER COLUMN "idPlayer" SET NOT NULL;
ALTER TABLE _player ALTER COLUMN "idPlayer" SET DEFAULT nextval('_player_idplayer_seq');
ALTER TABLE _player ALTER COLUMN "namePlayer" SET NOT NULL;
ALTER TABLE _player ALTER COLUMN country SET DEFAULT '';
UPDATE _player SET country = '' WHERE country IS NULL;
ALTER TABLE _player ALTER COLUMN country SET NOT NULL;
ALTER SEQUENCE _player_idplayer_seq OWNED BY _player."idPlayer";
SELECT setval('_player_idplayer_seq', GREATEST((SELECT COALESCE(MAX("idPlayer"), 0) FROM _player), 1), true);

CREATE SEQUENCE IF NOT EXISTS _tuningpart_idtuningpart_seq;
ALTER TABLE _tuningpart ALTER COLUMN "idTuningPart" TYPE integer;
ALTER TABLE _tuningpart ALTER COLUMN "idTuningPart" SET NOT NULL;
ALTER TABLE _tuningpart ALTER COLUMN "idTuningPart" SET DEFAULT nextval('_tuningpart_idtuningpart_seq');
ALTER TABLE _tuningpart ALTER COLUMN "nameTuningPart" SET NOT NULL;
ALTER SEQUENCE _tuningpart_idtuningpart_seq OWNED BY _tuningpart."idTuningPart";
SELECT setval('_tuningpart_idtuningpart_seq', GREATEST((SELECT COALESCE(MAX("idTuningPart"), 0) FROM _tuningpart), 1), true);

CREATE SEQUENCE IF NOT EXISTS _tuningsetup_idtuningsetup_seq;
ALTER TABLE _tuningsetup ALTER COLUMN "idTuningSetup" TYPE integer;
ALTER TABLE _tuningsetup ALTER COLUMN "idTuningSetup" SET NOT NULL;
ALTER TABLE _tuningsetup ALTER COLUMN "idTuningSetup" SET DEFAULT nextval('_tuningsetup_idtuningsetup_seq');
ALTER SEQUENCE _tuningsetup_idtuningsetup_seq OWNED BY _tuningsetup."idTuningSetup";
SELECT setval('_tuningsetup_idtuningsetup_seq', GREATEST((SELECT COALESCE(MAX("idTuningSetup"), 0) FROM _tuningsetup), 1), true);

ALTER TABLE _tuningsetupparts ALTER COLUMN "idTuningSetup" TYPE integer;
ALTER TABLE _tuningsetupparts ALTER COLUMN "idTuningPart" TYPE integer;
ALTER TABLE _tuningsetupparts ALTER COLUMN "idTuningSetup" SET NOT NULL;
ALTER TABLE _tuningsetupparts ALTER COLUMN "idTuningPart" SET NOT NULL;

ALTER TABLE _worldrecord ALTER COLUMN "idMap" TYPE integer;
ALTER TABLE _worldrecord ALTER COLUMN "idVehicle" TYPE integer;
ALTER TABLE _worldrecord ALTER COLUMN "idPlayer" TYPE integer;
ALTER TABLE _worldrecord ALTER COLUMN "idTuningSetup" DROP DEFAULT;
ALTER TABLE _worldrecord ALTER COLUMN "idTuningSetup" TYPE integer USING NULLIF("idTuningSetup", '')::integer;
ALTER TABLE _worldrecord ALTER COLUMN "idMap" SET NOT NULL;
ALTER TABLE _worldrecord ALTER COLUMN "idVehicle" SET NOT NULL;
ALTER TABLE _worldrecord ALTER COLUMN "idPlayer" SET NOT NULL;
ALTER TABLE _worldrecord ALTER COLUMN distance SET NOT NULL;
ALTER TABLE _worldrecord ALTER COLUMN current SET DEFAULT 1;
ALTER TABLE _worldrecord ALTER COLUMN current SET NOT NULL;
UPDATE _worldrecord SET questionable = 0 WHERE questionable IS NULL;
ALTER TABLE _worldrecord ALTER COLUMN questionable SET DEFAULT 0;
ALTER TABLE _worldrecord ALTER COLUMN questionable SET NOT NULL;
ALTER TABLE _worldrecord ADD COLUMN IF NOT EXISTS "idRecord" integer;
CREATE SEQUENCE IF NOT EXISTS _worldrecord_idrecord_seq;
UPDATE _worldrecord SET "idRecord" = nextval('_worldrecord_idrecord_seq') WHERE "idRecord" IS NULL;
ALTER TABLE _worldrecord ALTER COLUMN "idRecord" SET NOT NULL;
ALTER TABLE _worldrecord ALTER COLUMN "idRecord" SET DEFAULT nextval('_worldrecord_idrecord_seq');
ALTER SEQUENCE _worldrecord_idrecord_seq OWNED BY _worldrecord."idRecord";
SELECT setval('_worldrecord_idrecord_seq', GREATEST((SELECT COALESCE(MAX("idRecord"), 0) FROM _worldrecord), 1), true);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_map_pkey') THEN ALTER TABLE _map ADD CONSTRAINT _map_pkey PRIMARY KEY ("idMap"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_vehicle_pkey') THEN ALTER TABLE _vehicle ADD CONSTRAINT _vehicle_pkey PRIMARY KEY ("idVehicle"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_player_pkey') THEN ALTER TABLE _player ADD CONSTRAINT _player_pkey PRIMARY KEY ("idPlayer"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningpart_pkey') THEN ALTER TABLE _tuningpart ADD CONSTRAINT _tuningpart_pkey PRIMARY KEY ("idTuningPart"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetup_pkey') THEN ALTER TABLE _tuningsetup ADD CONSTRAINT _tuningsetup_pkey PRIMARY KEY ("idTuningSetup"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_pkey') THEN ALTER TABLE _tuningsetupparts ADD CONSTRAINT _tuningsetupparts_pkey PRIMARY KEY ("idTuningSetup", "idTuningPart"); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_pkey') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_pkey PRIMARY KEY ("idRecord"); END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS _map_namemap_unique ON _map ("nameMap");
CREATE UNIQUE INDEX IF NOT EXISTS _vehicle_namevehicle_unique ON _vehicle ("nameVehicle");
CREATE UNIQUE INDEX IF NOT EXISTS _player_nameplayer_unique ON _player ("namePlayer");
CREATE UNIQUE INDEX IF NOT EXISTS _tuningpart_nametuningpart_unique ON _tuningpart ("nameTuningPart");
CREATE UNIQUE INDEX IF NOT EXISTS _worldrecord_current_map_vehicle_unique ON _worldrecord ("idMap", "idVehicle") WHERE current = 1;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_current_check') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_current_check CHECK (current IN (0, 1)); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_questionable_check') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_questionable_check CHECK (questionable IN (0, 1)); END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_map_fk') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_map_fk FOREIGN KEY ("idMap") REFERENCES _map ("idMap") ON UPDATE CASCADE ON DELETE RESTRICT; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_vehicle_fk') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_vehicle_fk FOREIGN KEY ("idVehicle") REFERENCES _vehicle ("idVehicle") ON UPDATE CASCADE ON DELETE RESTRICT; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_player_fk') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_player_fk FOREIGN KEY ("idPlayer") REFERENCES _player ("idPlayer") ON UPDATE CASCADE ON DELETE RESTRICT; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_worldrecord_tuningsetup_fk') THEN ALTER TABLE _worldrecord ADD CONSTRAINT _worldrecord_tuningsetup_fk FOREIGN KEY ("idTuningSetup") REFERENCES _tuningsetup ("idTuningSetup") ON UPDATE CASCADE ON DELETE SET NULL; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_setup_fk') THEN ALTER TABLE _tuningsetupparts ADD CONSTRAINT _tuningsetupparts_setup_fk FOREIGN KEY ("idTuningSetup") REFERENCES _tuningsetup ("idTuningSetup") ON UPDATE CASCADE ON DELETE CASCADE; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '_tuningsetupparts_part_fk') THEN ALTER TABLE _tuningsetupparts ADD CONSTRAINT _tuningsetupparts_part_fk FOREIGN KEY ("idTuningPart") REFERENCES _tuningpart ("idTuningPart") ON UPDATE CASCADE ON DELETE RESTRICT; END IF;
END $$;

CREATE SEQUENCE IF NOT EXISTS news_id_seq;
CREATE TABLE IF NOT EXISTS news (
    id integer PRIMARY KEY DEFAULT nextval('news_id_seq'),
    title text NOT NULL,
    content text NOT NULL,
    author text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE news_id_seq OWNED BY news.id;
ALTER TABLE news ALTER COLUMN id SET DEFAULT nextval('news_id_seq');
INSERT INTO news (id, title, content, author, created_at)
SELECT id::integer, title, content, author,
       CASE WHEN NULLIF(created_at, '') IS NULL THEN CURRENT_TIMESTAMP ELSE created_at::timestamp END
FROM _news
WHERE title IS NOT NULL AND content IS NOT NULL
ON CONFLICT (id) DO NOTHING;
SELECT setval('news_id_seq', GREATEST((SELECT COALESCE(MAX(id), 0) FROM news), 1), true);

ALTER TABLE pendingsubmission ADD COLUMN IF NOT EXISTS tuningparts text;
ALTER TABLE pendingsubmission ALTER COLUMN id SET DEFAULT nextval('pendingsubmission_id_seq');
INSERT INTO pendingsubmission (id, idmap, idvehicle, distance, playername, playercountry, submitterip, status, submitted_at, tuningparts)
SELECT id::integer, "idMap"::integer, "idVehicle"::integer, distance, "playerName", "playerCountry", "submitterIp", COALESCE(status, 'pending'),
       CASE WHEN NULLIF(submitted_at, '') IS NULL THEN CURRENT_TIMESTAMP ELSE submitted_at::timestamp END,
       "tuningParts"
FROM _pendingsubmission
ON CONFLICT (id) DO NOTHING;
SELECT setval('pendingsubmission_id_seq', GREATEST((SELECT COALESCE(MAX(id), 0) FROM pendingsubmission), 1), true);
UPDATE pendingsubmission SET status = 'pending' WHERE status IS NULL OR status = '';
ALTER TABLE pendingsubmission ALTER COLUMN status SET DEFAULT 'pending';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = '_news') THEN
        ALTER TABLE _news SET SCHEMA legacy;
        ALTER TABLE legacy._news RENAME TO _news_archived;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = '_pendingsubmission') THEN
        ALTER TABLE _pendingsubmission SET SCHEMA legacy;
        ALTER TABLE legacy._pendingsubmission RENAME TO _pendingsubmission_archived;
    END IF;
END $$;

COMMIT;
