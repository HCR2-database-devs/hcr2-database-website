-- Un-mark Arena Gauntlet as a special map.
-- Mirrors the up migration for both the live `map` table and the legacy
-- `_map` copy that may exist on production.
DO $$
BEGIN
    IF to_regclass('public.map') IS NOT NULL THEN
        UPDATE map
        SET special = 0
        WHERE lower(name_map) = 'arena gauntlet'
          AND special = 1;
    END IF;
    IF to_regclass('public._map') IS NOT NULL THEN
        UPDATE _map
        SET special = 0
        WHERE upper("nameMap") = 'ARENA GAUNTLET'
          AND special = 1;
    END IF;
END $$;