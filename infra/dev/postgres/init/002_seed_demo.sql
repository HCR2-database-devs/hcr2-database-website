INSERT INTO map (id_map, name_map, special) VALUES
    (1, 'Countryside', 0),
    (2, 'Forest', 0),
    (3, 'Desert Valley', 0);

INSERT INTO vehicle (id_vehicle, name_vehicle) VALUES
    (1, 'Hill Climber'),
    (2, 'Motocross'),
    (3, 'Rally Car');

INSERT INTO player (id_player, name_player, country) VALUES
    (1, 'Demo Driver', 'United States'),
    (2, 'Sample Racer', 'Finland'),
    (3, 'QA Player', 'France');

INSERT INTO tuning_part (id_tuning_part, name_tuning_part) VALUES
    (1, 'Wings'),
    (2, 'Magnet'),
    (3, 'Coin Boost'),
    (4, 'Nitro'),
    (5, 'Wheelie Boost');

INSERT INTO tuning_setup (id_tuning_setup) VALUES
    (1),
    (2);

INSERT INTO tuning_setup_part (id_tuning_setup, id_tuning_part) VALUES
    (1, 1),
    (1, 2),
    (1, 4),
    (2, 1),
    (2, 3),
    (2, 5);

INSERT INTO world_record (
    id_record,
    id_map,
    id_vehicle,
    id_player,
    distance,
    current,
    id_tuning_setup,
    questionable,
    questionable_reason
) VALUES
    (1, 1, 1, 1, 12345, 1, 1, 0, NULL),
    (2, 2, 2, 2, 23456, 1, NULL, 1, 'Demo questionable note'),
    (3, 3, 3, 3, 34567, 1, 2, 0, NULL);

INSERT INTO pending_submission (
    id,
    id_map,
    id_vehicle,
    distance,
    player_name,
    player_country,
    tuning_parts,
    submitter_ip,
    status,
    submitted_at
) VALUES
    (
        1,
        1,
        2,
        13579,
        'Pending Demo',
        'Canada',
        'Wings, Magnet, Nitro',
        '203.0.113.10',
        'pending',
        CURRENT_TIMESTAMP - interval '10 minutes'
    ),
    (
        2,
        2,
        3,
        24680,
        'Already Approved Demo',
        'Germany',
        'Wings, Coin Boost, Wheelie Boost',
        '203.0.113.11',
        'approved',
        CURRENT_TIMESTAMP - interval '2 days'
    );

INSERT INTO news (id, title, content, author, created_at) VALUES
    (
        1,
        'Demo database ready',
        'This news item is seeded by the local development database.',
        'dev-seed',
        CURRENT_TIMESTAMP - interval '1 day'
    ),
    (
        2,
        'Read-only endpoints can be tested',
        'Maps, vehicles, players, tuning parts, records and news all have demo rows.',
        'dev-seed',
        CURRENT_TIMESTAMP
    );

SELECT setval('map_id_seq', (SELECT max(id_map) FROM map));
SELECT setval('vehicle_id_seq', (SELECT max(id_vehicle) FROM vehicle));
SELECT setval('player_id_seq', (SELECT max(id_player) FROM player));
SELECT setval('tuning_part_id_seq', (SELECT max(id_tuning_part) FROM tuning_part));
SELECT setval('tuning_setup_id_seq', (SELECT max(id_tuning_setup) FROM tuning_setup));
SELECT setval('world_record_id_seq', (SELECT max(id_record) FROM world_record));
SELECT setval('pending_submission_id_seq', (SELECT max(id) FROM pending_submission));
SELECT setval('news_id_seq', (SELECT max(id) FROM news));
