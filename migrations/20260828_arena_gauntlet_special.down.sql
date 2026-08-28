-- Un-mark Arena Gauntlet as a special map.
UPDATE _map
SET special = 0
WHERE upper("nameMap") = 'ARENA GAUNTLET'
  AND special = 1;