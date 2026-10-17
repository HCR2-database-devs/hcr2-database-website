ALTER TABLE community_username_history
    ADD COLUMN override_bad_words boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN note text;
