BEGIN;

ALTER TABLE _map OWNER TO hcr2user;
ALTER TABLE _vehicle OWNER TO hcr2user;
ALTER TABLE _player OWNER TO hcr2user;
ALTER TABLE _tuningpart OWNER TO hcr2user;
ALTER TABLE _tuningsetup OWNER TO hcr2user;
ALTER TABLE _tuningsetupparts OWNER TO hcr2user;
ALTER TABLE _worldrecord OWNER TO hcr2user;

COMMIT;
