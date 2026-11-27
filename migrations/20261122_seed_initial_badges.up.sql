INSERT INTO badge_category (identifier, name, description, sort_order)
VALUES
    ('team', 'Team', 'Roles and responsibilities within the HCR2.xyz team.', 10),
    ('community', 'Community', 'Participation, recognition and community milestones.', 20),
    ('hcr2', 'HCR2', 'Achievements based on verified HCR2 record data.', 30),
    ('submission', 'Submissions', 'Milestones for accepted record submissions.', 40)
ON CONFLICT (identifier) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    enabled = TRUE;

INSERT INTO badge (
    identifier, category_id, name, description, icon_path, badge_type, award_method,
    rarity, requirement_type, requirement_config, enabled, hidden_until_unlocked,
    revocable, featureable, permanent, sort_order
)
SELECT
    v.identifier,
    c.id,
    v.name,
    v.description,
    '/img/badges/' || v.identifier || '.webp',
    v.badge_type,
    v.award_method,
    v.rarity,
    v.requirement_type,
    v.requirement_config::jsonb,
    TRUE,
    FALSE,
    TRUE,
    TRUE,
    v.permanent,
    v.sort_order
FROM (
    VALUES
        ('owner', 'team', 'Owner', 'Owner of HCR2.xyz.', 'team', 'manual', 'legendary', NULL, '{}', TRUE, 10),
        ('developer', 'team', 'Developer', 'Contributes to developing and maintaining HCR2.xyz.', 'team', 'manual', 'epic', NULL, '{}', TRUE, 20),
        ('administrator', 'team', 'Administrator', 'Helps manage the website and its community.', 'team', 'manual', 'epic', NULL, '{}', TRUE, 30),
        ('moderator', 'team', 'Moderator', 'Helps moderate the HCR2.xyz community.', 'team', 'manual', 'rare', NULL, '{}', TRUE, 40),
        ('staff', 'team', 'Staff', 'Member of the HCR2.xyz staff team.', 'team', 'manual', 'rare', NULL, '{}', TRUE, 50),
        ('beta_tester', 'community', 'Beta Tester', 'Participated in testing HCR2.xyz beta features.', 'community', 'manual', 'uncommon', NULL, '{}', TRUE, 110),
        ('early_supporter', 'community', 'Early Supporter', 'Supported the website during its early development.', 'community', 'manual', 'rare', NULL, '{}', TRUE, 120),
        ('founding_member', 'community', 'Founding Member', 'Was part of the original HCR2.xyz community.', 'community', 'manual', 'epic', NULL, '{}', TRUE, 130),
        ('contributor', 'community', 'Contributor', 'Made a meaningful contribution to the website.', 'special_recognition', 'manual', 'rare', NULL, '{}', TRUE, 140),
        ('helpful_member', 'community', 'Helpful Member', 'Recognized for helping the community.', 'special_recognition', 'manual', 'uncommon', NULL, '{}', TRUE, 150),
        ('verified_player', 'hcr2', 'Verified Player', 'Successfully verified an HCR2 player identity.', 'achievement', 'automatic', 'uncommon', 'hcr2_identity_verified', '{}', TRUE, 210),
        ('first_world_record', 'hcr2', 'First World Record', 'Held a verified World Record for the first time.', 'achievement', 'automatic', 'rare', 'world_records_ever_count', '{"count":1}', TRUE, 220),
        ('world_record_holder', 'hcr2', 'World Record Holder', 'Currently holds at least one verified World Record.', 'achievement', 'automatic', 'rare', 'world_records_current_count', '{"count":1}', FALSE, 230),
        ('record_collector', 'hcr2', 'Record Collector', 'Currently holds at least 5 verified World Records.', 'achievement', 'automatic', 'epic', 'world_records_current_count', '{"count":5}', FALSE, 240),
        ('record_expert', 'hcr2', 'Record Expert', 'Currently holds at least 10 verified World Records.', 'achievement', 'automatic', 'epic', 'world_records_current_count', '{"count":10}', FALSE, 250),
        ('record_legend', 'hcr2', 'Record Legend', 'Currently holds at least 25 verified World Records.', 'achievement', 'automatic', 'legendary', 'world_records_current_count', '{"count":25}', FALSE, 260),
        ('record_master', 'hcr2', 'Record Master', 'Currently holds at least 50 verified World Records.', 'achievement', 'automatic', 'legendary', 'world_records_current_count', '{"count":50}', FALSE, 270),
        ('first_submission', 'submission', 'First Submission', 'First accepted record submission.', 'achievement', 'automatic', 'uncommon', 'approved_submissions_count', '{"count":1}', TRUE, 310),
        ('submission_contributor', 'submission', 'Submission Contributor', '10 accepted record submissions.', 'achievement', 'automatic', 'rare', 'approved_submissions_count', '{"count":10}', TRUE, 320),
        ('dedicated_contributor', 'submission', 'Dedicated Contributor', '50 accepted record submissions.', 'achievement', 'automatic', 'epic', 'approved_submissions_count', '{"count":50}', TRUE, 330),
        ('archive_contributor', 'submission', 'Archive Contributor', '100 accepted record submissions.', 'achievement', 'automatic', 'legendary', 'approved_submissions_count', '{"count":100}', TRUE, 340),
        ('veteran', 'community', 'Veteran', 'Has been a community member for at least one year.', 'achievement', 'automatic', 'rare', 'membership_duration_days', '{"days":365}', TRUE, 160),
        ('community_contributor', 'community', 'Community Contributor', 'Reached a meaningful community contribution threshold.', 'achievement', 'automatic', 'epic', 'xp_total', '{"amount":500}', TRUE, 170)
) AS v(identifier, category_identifier, name, description, badge_type, award_method, rarity, requirement_type, requirement_config, permanent, sort_order)
JOIN badge_category c ON c.identifier = v.category_identifier
ON CONFLICT (identifier) DO UPDATE SET
    category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    icon_path = EXCLUDED.icon_path,
    badge_type = EXCLUDED.badge_type,
    award_method = EXCLUDED.award_method,
    rarity = EXCLUDED.rarity,
    requirement_type = EXCLUDED.requirement_type,
    requirement_config = EXCLUDED.requirement_config,
    enabled = TRUE,
    permanent = EXCLUDED.permanent,
    sort_order = EXCLUDED.sort_order,
    archived_at = NULL,
    updated_at = CURRENT_TIMESTAMP;
