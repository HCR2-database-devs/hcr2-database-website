SET search_path = public;

ALTER TABLE tuning_setup
    ADD COLUMN IF NOT EXISTS echo_affected_part_id integer,
    ADD CONSTRAINT tuning_setup_echo_part_fk
        FOREIGN KEY (echo_affected_part_id)
        REFERENCES tuning_part (id_tuning_part)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
