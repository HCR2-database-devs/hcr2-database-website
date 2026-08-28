-- Mark Arena Gauntlet as a special map.
UPDATE _map
SET special = 1
WHERE upper("nameMap") = 'ARENA GAUNTLET'
  AND special <> 1;