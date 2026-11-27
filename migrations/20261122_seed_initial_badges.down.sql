DELETE FROM badge WHERE identifier = ANY (ARRAY[
    'owner', 'developer', 'administrator', 'moderator', 'staff',
    'beta_tester', 'early_supporter', 'founding_member', 'contributor', 'helpful_member',
    'verified_player', 'first_world_record', 'world_record_holder', 'record_collector',
    'record_expert', 'record_legend', 'record_master',
    'first_submission', 'submission_contributor', 'dedicated_contributor', 'archive_contributor',
    'veteran', 'community_contributor'
]::text[]);

DELETE FROM badge_category
WHERE identifier = ANY (ARRAY['team', 'community', 'hcr2', 'submission']::text[])
  AND NOT EXISTS (SELECT 1 FROM badge WHERE badge.category_id = badge_category.id);
