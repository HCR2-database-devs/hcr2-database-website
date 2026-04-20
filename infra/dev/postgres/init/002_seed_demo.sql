INSERT INTO _map (idmap, namemap, special) VALUES
    (1, 'Countryside', 0),
    (2, 'Forest', 0),
    (3, 'Desert Valley', 0);

INSERT INTO _vehicle (idvehicle, namevehicle) VALUES
    (1, 'Hill Climber'),
    (2, 'Motocross'),
    (3, 'Rally Car');

INSERT INTO _player (idplayer, nameplayer, country) VALUES
    (1, 'Demo Driver', 'United States'),
    (2, 'Sample Racer', 'Finland'),
    (3, 'QA Player', 'France');

INSERT INTO _tuningpart (idtuningpart, nametuningpart) VALUES
    (1, 'Wings'),
    (2, 'Magnet'),
    (3, 'Coin Boost'),
    (4, 'Nitro'),
    (5, 'Wheelie Boost');

INSERT INTO _tuningsetup (idtuningsetup) VALUES
    (1),
    (2);

INSERT INTO _tuningsetupparts (idtuningsetup, idtuningpart) VALUES
    (1, 1),
    (1, 2),
    (1, 4),
    (2, 1),
    (2, 3),
    (2, 5);

INSERT INTO _worldrecord (
    idrecord,
    idmap,
    idvehicle,
    idplayer,
    distance,
    current,
    idtuningsetup,
    questionable,
    questionable_reason
) VALUES
    (1, 1, 1, 1, 12345, 1, 1, 0, NULL),
    (2, 2, 2, 2, 23456, 1, NULL, 1, 'Demo questionable note'),
    (3, 3, 3, 3, 34567, 1, 2, 0, NULL);

INSERT INTO pendingsubmission (
    id,
    idmap,
    idvehicle,
    distance,
    playername,
    playercountry,
    tuningparts,
    submitterip,
    status,
    submitted_at
) VALUES
    (1, 1, 2, 13579, 'Pending Demo', 'Canada', 'Wings, Magnet, Nitro', '203.0.113.10', 'pending', now() - interval '10 minutes'),
    (2, 2, 3, 24680, 'Already Approved Demo', 'Germany', 'Wings, Coin Boost, Wheelie Boost', '203.0.113.11', 'approved', now() - interval '2 days');

INSERT INTO news (id, title, content, author, created_at) VALUES
    (1, 'Demo database ready', 'This news item is seeded by the local development database.', 'dev-seed', now() - interval '1 day'),
    (2, 'Read-only endpoints can be tested', 'Maps, vehicles, players, tuning parts, records and news all have demo rows.', 'dev-seed', now());

SELECT setval(pg_get_serial_sequence('_tuningpart', 'idtuningpart'), (SELECT max(idtuningpart) FROM _tuningpart));
SELECT setval(pg_get_serial_sequence('_tuningsetup', 'idtuningsetup'), (SELECT max(idtuningsetup) FROM _tuningsetup));
SELECT setval(pg_get_serial_sequence('_worldrecord', 'idrecord'), (SELECT max(idrecord) FROM _worldrecord));
SELECT setval(pg_get_serial_sequence('pendingsubmission', 'id'), (SELECT max(id) FROM pendingsubmission));
SELECT setval(pg_get_serial_sequence('news', 'id'), (SELECT max(id) FROM news));
