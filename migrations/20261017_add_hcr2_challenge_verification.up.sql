-- Verification method C: playhcr.com jeep challenge.
--
-- The user is asked to drive a server-assigned random distance (1-2000 m) with
-- a jeep in Countryside Adventure and to send the link to the playhcr.com
-- challenge they made from it. An administrator still reads the challenge and
-- decides; nothing here verifies anything by itself.

ALTER TABLE hcr2_verification_request
    ADD COLUMN IF NOT EXISTS challenge_distance_m integer,
    ADD COLUMN IF NOT EXISTS challenge_url text,
    ADD COLUMN IF NOT EXISTS challenge_id text,
    ADD COLUMN IF NOT EXISTS challenge_confirmed_at timestamp without time zone;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_challenge_distance_check
        CHECK (challenge_distance_m IS NULL
               OR challenge_distance_m BETWEEN 1 AND 2000);

-- Only a playhcr.com challenge link may be stored. Enforced in the database as
-- well as in the service so a direct write cannot store anything else.
ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_challenge_url_check
        CHECK (challenge_url IS NULL
               OR challenge_url LIKE 'https://playhcr.com/challenge?id=%');

-- The distance is stored as soon as the method is chosen, before the run
-- happens. The link, its id and the confirmation timestamp are one proof and
-- are therefore written together, and only once a distance exists.
ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_challenge_complete_check
        CHECK ((challenge_url IS NULL AND challenge_id IS NULL
                AND challenge_confirmed_at IS NULL)
               OR (challenge_distance_m IS NOT NULL AND challenge_url IS NOT NULL
                   AND challenge_id IS NOT NULL AND challenge_confirmed_at IS NOT NULL));

ALTER TABLE hcr2_account_link
    DROP CONSTRAINT IF EXISTS hcr2_account_link_method_check;

ALTER TABLE hcr2_account_link
    ADD CONSTRAINT hcr2_account_link_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share', 'playhcr_challenge'));

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_method_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share', 'playhcr_challenge'));

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_step_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'challenge_assign', 'challenge_link',
                        'summary'));

ALTER TABLE hcr2_verification_request_step
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_step_step_check;

ALTER TABLE hcr2_verification_request_step
    ADD CONSTRAINT hcr2_verification_request_step_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'challenge_assign', 'challenge_link',
                        'summary', 'submitted', 'approved',
                        'rejected', 'expired', 'cancelled', 'retry_requested'));

ALTER TABLE hcr2_verification_request
    DROP CONSTRAINT IF EXISTS hcr2_verification_request_rejection_category_check;

ALTER TABLE hcr2_verification_request
    ADD CONSTRAINT hcr2_verification_request_rejection_category_check
        CHECK (rejection_category IS NULL OR rejection_category IN (
            'code_not_visible', 'wrong_player_name', 'could_not_confirm_account',
            'screen_share_inconclusive', 'challenge_mismatch', 'name_already_linked',
            'no_contact', 'request_cancelled', 'other'
        ));