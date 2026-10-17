-- Reverts verification method C (playhcr.com jeep challenge).
--
-- Only safe once no request or link uses the method: the method CHECK
-- constraints are restored to the two original methods, so any surviving
-- 'playhcr_challenge' row would block this. Check before applying:
--
--   SELECT count(*) FROM hcr2_verification_request
--     WHERE verification_method = 'playhcr_challenge';
--   SELECT count(*) FROM hcr2_account_link
--     WHERE verification_method = 'playhcr_challenge';

DELETE FROM hcr2_verification_request_step
    WHERE step IN ('challenge_assign', 'challenge_link');

-- Requests that chose the method but never submitted can simply go; anything
-- already submitted or decided is left in place and will be rejected by the
-- restored method constraint below, which is the loud, correct outcome.
DELETE FROM hcr2_verification_request
    WHERE verification_method = 'playhcr_challenge'
      AND status IN ('draft', 'in_progress', 'expired', 'cancelled');

DELETE FROM hcr2_account_link
    WHERE verification_method = 'playhcr_challenge';

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_challenge_complete_check,
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_challenge_url_check,
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_challenge_distance_check;

ALTER TABLE hcr2_verification_request
    DROP COLUMN IF EXISTS challenge_distance_m,
    DROP COLUMN IF EXISTS challenge_url,
    DROP COLUMN IF EXISTS challenge_id,
    DROP COLUMN IF EXISTS challenge_confirmed_at;

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_rejection_category_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_rejection_category_check
        CHECK (rejection_category IS NULL OR rejection_category IN (
            'code_not_visible', 'wrong_player_name', 'could_not_confirm_account',
            'screen_share_inconclusive', 'name_already_linked', 'no_contact',
            'request_cancelled', 'other'
        ));

ALTER TABLE hcr2_verification_request_step
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_step_step_check;

ALTER TABLE hcr2_verification_request_step
    ADD CONSTRAINT hcr2_verification_request_step_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'summary', 'submitted', 'approved',
                        'rejected', 'expired', 'cancelled', 'retry_requested'));

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_step_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'summary'));

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_method_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share'));

ALTER TABLE hcr2_account_link
    DROP CONSTRAINT IF EXISTS hcr2_account_link_method_check;

ALTER TABLE hcr2_account_link
    ADD CONSTRAINT hcr2_account_link_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share'));