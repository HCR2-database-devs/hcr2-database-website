ALTER TABLE activity_log DROP COLUMN IF EXISTS note;

DROP TABLE IF EXISTS community_profile_report;
DROP SEQUENCE IF EXISTS community_profile_report_id_seq;

ALTER TABLE community_user
    DROP COLUMN IF EXISTS bio,
    DROP COLUMN IF EXISTS country,
    DROP COLUMN IF EXISTS favorite_vehicle_id,
    DROP COLUMN IF EXISTS favorite_map_id,
    DROP COLUMN IF EXISTS banner_content,
    DROP COLUMN IF EXISTS banner_content_type,
    DROP COLUMN IF EXISTS banner_updated_at,
    DROP COLUMN IF EXISTS profile_public,
    DROP COLUMN IF EXISTS show_country,
    DROP COLUMN IF EXISTS show_bio,
    DROP COLUMN IF EXISTS show_favorite_vehicle,
    DROP COLUMN IF EXISTS show_favorite_map,
    DROP COLUMN IF EXISTS admin_disabled;