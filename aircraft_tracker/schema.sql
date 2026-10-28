CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_code CHAR(2) UNIQUE NOT NULL,
    lat_min DOUBLE PRECISION NOT NULL,
    lat_max DOUBLE PRECISION NOT NULL,
    lon_min DOUBLE PRECISION NOT NULL,
    lon_max DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS aeroplanes (
    id BIGSERIAL PRIMARY KEY,
    icao24 VARCHAR(6) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    callsign VARCHAR(16),
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    velocity DOUBLE PRECISION,
    on_ground BOOLEAN,
    last_contact BIGINT,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_country_id
    ON aeroplanes(country_id);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_icao24
    ON aeroplanes(icao24);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_callsign
    ON aeroplanes(callsign);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_collected_at
    ON aeroplanes(collected_at);
