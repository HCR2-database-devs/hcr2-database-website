CREATE SEQUENCE changelog_id_seq;
CREATE TABLE changelog (
    id integer PRIMARY KEY DEFAULT nextval('changelog_id_seq'),
    version text NOT NULL,
    title text,
    added text[] NOT NULL DEFAULT '{}',
    changed text[] NOT NULL DEFAULT '{}',
    fixed text[] NOT NULL DEFAULT '{}',
    author text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE changelog_id_seq OWNED BY changelog.id;

CREATE INDEX changelog_created_at_id_desc_idx ON changelog (created_at DESC, id DESC);

INSERT INTO changelog (version, title, added, changed, fixed, author) VALUES
(
    '0.2.0',
    'Site update',
    ARRAY[
        'Google Ads and ad slots across pages',
        'Donators banner',
        'Partners and staff updates',
        'Admin activity log',
        'Mythic records page',
        'New statistics page'
    ],
    ARRAY[
        'Improved mobile navigation',
        'Faster and more reliable record status editing'
    ],
    ARRAY[
        'Record status and note editing no longer crash on invalid JSON',
        'Statistics bugs',
        'News time display',
        'Maintenance toggle',
        'Copy button',
        'Dropdown menus on mobile'
    ],
    'Changelog'
),
(
    '0.1.0',
    'Launch',
    ARRAY[
        'Initial records database with maps, vehicles, players and tuning parts'
    ],
    ARRAY[]::text[],
    ARRAY[]::text[],
    'Changelog'
);