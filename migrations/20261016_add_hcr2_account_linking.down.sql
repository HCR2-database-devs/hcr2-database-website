ALTER TABLE community_user
    DROP COLUMN IF EXISTS show_hcr2_player_name;

DROP INDEX IF EXISTS idx_player_name_lower_prefix;

DROP TABLE IF EXISTS community_action_rate_limit;

DROP TABLE IF EXISTS hcr2_verification_request_step;
DROP SEQUENCE IF EXISTS hcr2_verification_request_step_id_seq;

DROP TABLE IF EXISTS hcr2_verification_request;
DROP SEQUENCE IF EXISTS hcr2_verification_request_id_seq;

DROP TABLE IF EXISTS hcr2_account_link;
DROP SEQUENCE IF EXISTS hcr2_account_link_id_seq;