BEGIN;

-- Repair mojibake produced when UTF-8 bytes were decoded as latin1/cp1252.
-- This targets only rows that show common mojibake markers.
CREATE OR REPLACE FUNCTION repair_mojibake_text(input_text text)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    converted text;
BEGIN
    IF input_text IS NULL OR input_text = '' THEN
        RETURN input_text;
    END IF;

    BEGIN
        converted := convert_from(convert_to(input_text, 'LATIN1'), 'UTF8');
    EXCEPTION
        WHEN character_not_in_repertoire OR untranslatable_character THEN
            RETURN input_text;
    END;

    IF (
        length(input_text) - length(replace(input_text, 'Ã', ''))
        + length(input_text) - length(replace(input_text, 'Â', ''))
        + length(input_text) - length(replace(input_text, 'â', ''))
        + length(input_text) - length(replace(input_text, 'ð', ''))
    ) > (
        length(converted) - length(replace(converted, 'Ã', ''))
        + length(converted) - length(replace(converted, 'Â', ''))
        + length(converted) - length(replace(converted, 'â', ''))
        + length(converted) - length(replace(converted, 'ð', ''))
    ) THEN
        RETURN converted;
    END IF;

    RETURN input_text;
END;
$$;

UPDATE news
SET
    title = repair_mojibake_text(title),
    content = repair_mojibake_text(content),
    author = repair_mojibake_text(author)
WHERE
    title LIKE '%Ã%' OR title LIKE '%Â%' OR title LIKE '%â%' OR title LIKE '%ð%'
    OR content LIKE '%Ã%' OR content LIKE '%Â%' OR content LIKE '%â%' OR content LIKE '%ð%'
    OR author LIKE '%Ã%' OR author LIKE '%Â%' OR author LIKE '%â%' OR author LIKE '%ð%';

DO $$
BEGIN
    IF to_regclass('_news') IS NOT NULL THEN
        EXECUTE '
            UPDATE _news
            SET
                title = repair_mojibake_text(title),
                content = repair_mojibake_text(content),
                author = repair_mojibake_text(author)
            WHERE
                title LIKE ''%Ã%'' OR title LIKE ''%Â%'' OR title LIKE ''%â%'' OR title LIKE ''%ð%''
                OR content LIKE ''%Ã%'' OR content LIKE ''%Â%'' OR content LIKE ''%â%'' OR content LIKE ''%ð%''
                OR author LIKE ''%Ã%'' OR author LIKE ''%Â%'' OR author LIKE ''%â%'' OR author LIKE ''%ð%''
        ';
    END IF;
END;
$$;

DROP FUNCTION repair_mojibake_text(text);

COMMIT;
