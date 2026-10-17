BEGIN;

-- Trim surrounding whitespace from legacy country values.
UPDATE player SET country = btrim(country) WHERE country IS DISTINCT FROM btrim(country);

-- Blank out junk values that contain no letters (e.g. "___", "???", emoji/flag-only).
UPDATE player
SET country = ''
WHERE country <> ''
  AND NOT (country ~ '[A-Za-z]');

-- Title-case all-lowercase plain text values (e.g. "poland" -> "Poland"),
-- leaving subregion codes (e.g. "gb-eng", "us-tx") and "other countries" untouched.
UPDATE player
SET country = initcap(country)
WHERE country ~ '^[a-z]+([ -][a-z]+)*$'
  AND NOT (country ~ '^[a-z]{2}-[a-z]{1,3}$')
  AND lower(country) <> 'other countries';

COMMIT;