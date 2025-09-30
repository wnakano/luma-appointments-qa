CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- gen_random_uuid()

CREATE TABLE clinic (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT NOT NULL,
  address_line1    TEXT,
  address_line2    TEXT,
  city             TEXT,
  state            TEXT,
  postal_code      TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE provider (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id        UUID NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
  full_name        TEXT NOT NULL,
  specialty        TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE patient (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name        TEXT NOT NULL,
  phone            VARCHAR(20) NOT NULL,
  date_of_birth    DATE NOT NULL,
  email            TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_patients_phone UNIQUE (phone),
  CONSTRAINT ck_phone_format CHECK (phone ~ '^\+?[1-9][0-9]{7,14}$')
);

CREATE INDEX idx_patients_verification
  ON patient (phone, date_of_birth, lower(full_name));


CREATE TABLE appointment (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id       UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  clinic_id        UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
  provider_id      UUID NOT NULL REFERENCES provider(id) ON DELETE RESTRICT,
  starts_at        TIMESTAMPTZ NOT NULL,
  ends_at          TIMESTAMPTZ NOT NULL,
  reason           TEXT,
  status           TEXT NOT NULL DEFAULT 'scheduled',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_time_order CHECK (ends_at > starts_at),
  CONSTRAINT ck_status CHECK (status IN ('scheduled','confirmed','canceled_by_patient','canceled_by_clinic'))
);

CREATE TYPE menu_choices AS ENUM (
  'USER_VERIFICATION',
  'LIST',
  'CONFIRM',
  'CANCEL',
  'RESCHEDULE',
  'ROUTING'
);

-- CREATE TABLE message(
--   id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   conversation_id  UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
--   request_id       UUID NOT NULL,
--   user_message     TEXT NOT NULL,
--   latency_ms       INT,
--   menu_choice      menu_choices NOT NULL,
--   input_tokens     INT NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
--   output_tokens    INT NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
--   total_tokens     INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
--   system_message   TEXT NOT NULL,
--   started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
--   completed_at     TIMESTAMPTZ,
-- );

-- CREATE TABLE conversation(
--   id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   session_id       UUID NOT NULL,
--   qa_system        TEXT NOT NULL,
--   messages         message[] NOT NULL DEFAULT '{}',
--   created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
--   updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
-- );