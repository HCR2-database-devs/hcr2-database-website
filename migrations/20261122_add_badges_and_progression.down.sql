ALTER TABLE community_user DROP COLUMN show_xp;
ALTER TABLE community_user DROP COLUMN show_badges;

DROP TABLE IF EXISTS progression_evaluation;
DROP TABLE IF EXISTS progression_event;
DROP TABLE IF EXISTS xp_transaction;
DROP SEQUENCE IF EXISTS xp_transaction_id_seq;
DROP TABLE IF EXISTS community_progression;
DROP TABLE IF EXISTS featured_badge;
DROP SEQUENCE IF EXISTS featured_badge_id_seq;
DROP TABLE IF EXISTS badge_progress;
DROP TABLE IF EXISTS badge_award_history;
DROP SEQUENCE IF EXISTS badge_award_history_id_seq;
DROP TABLE IF EXISTS community_user_badge;
DROP SEQUENCE IF EXISTS community_user_badge_id_seq;
DROP TABLE IF EXISTS badge;
DROP SEQUENCE IF EXISTS badge_id_seq;
DROP TABLE IF EXISTS badge_category;
DROP SEQUENCE IF EXISTS badge_category_id_seq;
