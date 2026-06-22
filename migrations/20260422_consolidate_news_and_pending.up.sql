BEGIN;

-- Consolidate news data from legacy table into canonical table.
INSERT INTO news (id, title, content, author, created_at)
SELECT
    id::integer,
    title,
    content,
    author,
    CASE
        WHEN NULLIF(created_at, '') IS NULL THEN CURRENT_TIMESTAMP
        ELSE created_at::timestamp
    END
FROM _news
WHERE title IS NOT NULL
  AND content IS NOT NULL
ON CONFLICT (id) DO UPDATE
SET
    title = EXCLUDED.title,
    content = EXCLUDED.content,
    author = COALESCE(EXCLUDED.author, news.author),
    created_at = COALESCE(EXCLUDED.created_at, news.created_at);

UPDATE news SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

ALTER TABLE news
    ALTER COLUMN id SET NOT NULL,
    ALTER COLUMN title SET NOT NULL,
    ALTER COLUMN content SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS news_created_at_id_desc_idx ON news (created_at DESC, id DESC);

-- Consolidate pending submissions into canonical table.
ALTER TABLE pendingsubmission ADD COLUMN IF NOT EXISTS tuningparts text;

INSERT INTO pendingsubmission (
    id,
    idmap,
    idvehicle,
    distance,
    playername,
    playercountry,
    submitterip,
    status,
    submitted_at,
    tuningparts
)
SELECT
    id::integer,
    "idMap"::integer,
    "idVehicle"::integer,
    distance,
    "playerName",
    "playerCountry",
    "submitterIp",
    CASE
        WHEN status IN ('pending', 'approved', 'rejected') THEN status
        ELSE 'pending'
    END,
    CASE
        WHEN NULLIF(submitted_at, '') IS NULL THEN CURRENT_TIMESTAMP
        ELSE submitted_at::timestamp
    END,
    "tuningParts"
FROM _pendingsubmission
ON CONFLICT (id) DO UPDATE
SET
    idmap = EXCLUDED.idmap,
    idvehicle = EXCLUDED.idvehicle,
    distance = EXCLUDED.distance,
    playername = EXCLUDED.playername,
    playercountry = EXCLUDED.playercountry,
    submitterip = EXCLUDED.submitterip,
    status = EXCLUDED.status,
    submitted_at = EXCLUDED.submitted_at,
    tuningparts = EXCLUDED.tuningparts;

UPDATE pendingsubmission
SET status = 'pending'
WHERE status IS NULL
   OR status = ''
   OR status NOT IN ('pending', 'approved', 'rejected');

UPDATE pendingsubmission
SET submitted_at = CURRENT_TIMESTAMP
WHERE submitted_at IS NULL;

ALTER TABLE pendingsubmission
    ALTER COLUMN id SET NOT NULL,
    ALTER COLUMN idmap SET NOT NULL,
    ALTER COLUMN idvehicle SET NOT NULL,
    ALTER COLUMN distance SET NOT NULL,
    ALTER COLUMN playername SET NOT NULL,
    ALTER COLUMN playercountry SET NOT NULL,
    ALTER COLUMN submitterip SET NOT NULL,
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN submitted_at SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'pending',
    ALTER COLUMN submitted_at SET DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'pendingsubmission_status_check'
    ) THEN
        ALTER TABLE pendingsubmission
        ADD CONSTRAINT pendingsubmission_status_check
        CHECK (status IN ('pending', 'approved', 'rejected'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS pendingsubmission_status_submitted_idx
    ON pendingsubmission (status, submitted_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS pendingsubmission_map_vehicle_idx
    ON pendingsubmission (idmap, idvehicle);

SELECT setval(
    'news_id_seq',
    GREATEST((SELECT COALESCE(MAX(id), 0) FROM news), 1),
    true
);

SELECT setval(
    'pendingsubmission_id_seq',
    GREATEST((SELECT COALESCE(MAX(id), 0) FROM pendingsubmission), 1),
    true
);

COMMIT;
