-- Floor-plan drawings get a kind, revisions and an original (PDF) source file; assets are pinned on them.
-- Columns on the existing floor_plan table are nullable with no FK: Canvas refuses new constraints there.
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS kind VARCHAR(32);
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS revision VARCHAR(32);
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS source_file_id BIGINT;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS superseded_by_id BIGINT;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS created_by BIGINT;

CREATE SEQUENCE IF NOT EXISTS floor_plan_pin_seq START WITH 1 INCREMENT BY 50;

-- x and y are fractions (0..1) of the drawing's width and height.
CREATE TABLE IF NOT EXISTS floor_plan_pin (
    id BIGINT NOT NULL DEFAULT nextval('floor_plan_pin_seq'),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by BIGINT,
    updated_by BIGINT,
    company_id BIGINT NOT NULL REFERENCES company (id) ON DELETE CASCADE,
    floor_plan_id BIGINT NOT NULL REFERENCES floor_plan (id) ON DELETE CASCADE,
    asset_id BIGINT NOT NULL REFERENCES asset (id) ON DELETE CASCADE,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_floor_plan_pin UNIQUE (floor_plan_id, asset_id)
);

CREATE INDEX IF NOT EXISTS ix_floor_plan_pin_floor_plan_id ON floor_plan_pin (floor_plan_id);
CREATE INDEX IF NOT EXISTS ix_floor_plan_pin_asset_id ON floor_plan_pin (asset_id);
