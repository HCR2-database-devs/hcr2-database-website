ALTER TABLE pending_submission
    ALTER COLUMN submitter_ip DROP NOT NULL;

ALTER TABLE pending_submission
    ADD COLUMN submitter_community_user_id integer;

ALTER TABLE pending_submission
    ADD CONSTRAINT pending_submission_submitter_community_user_fk
    FOREIGN KEY (submitter_community_user_id)
    REFERENCES community_user (id)
    ON DELETE SET NULL;

CREATE INDEX pending_submission_submitter_community_user_idx
    ON pending_submission (submitter_community_user_id);

ALTER TABLE world_record
    ADD COLUMN submitter_community_user_id integer;

ALTER TABLE world_record
    ADD CONSTRAINT world_record_submitter_community_user_fk
    FOREIGN KEY (submitter_community_user_id)
    REFERENCES community_user (id)
    ON DELETE SET NULL;

CREATE INDEX world_record_submitter_community_user_idx
    ON world_record (submitter_community_user_id);

CREATE TABLE public_submission_rate_limit (
    rate_key text PRIMARY KEY,
    request_count integer NOT NULL DEFAULT 1,
    window_started_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT public_submission_rate_limit_count_positive CHECK (request_count > 0)
);

CREATE INDEX public_submission_rate_limit_window_idx
    ON public_submission_rate_limit (window_started_at);
