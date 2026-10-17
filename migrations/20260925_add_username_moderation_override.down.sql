ALTER TABLE community_username_history
    DROP COLUMN IF EXISTS note,
    DROP COLUMN IF EXISTS override_bad_words;
