-- Mark Arena Gauntlet as a special map.
-- The live schema uses table `map` with snake_case `name_map`; a legacy
-- `_map` ("nameMap") copy may also exist on production, so both are handled.
DO $$
BEGIN
    IF to_regclass('public.map') IS NOT NULL THEN
        UPDATE map
        SET special = 1
        WHERE lower(name_map) = 'arena gauntlet'
          AND special <> 1;
    END IF;
    IF to_regclass('public._map') IS NOT NULL THEN
        UPDATE _map
        SET special = 1
        WHERE upper("nameMap") = 'ARENA GAUNTLET'
          AND special <> 1;
    END IF;
END $$;