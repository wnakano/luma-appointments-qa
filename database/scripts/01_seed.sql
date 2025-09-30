-- seed.sql
-- Populate clinics, provider, patient, and appointment with realistic data,
-- but only if there are no patient yet.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM patient) THEN

    -- 0) Extensions
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    -- 1) Clinics
    INSERT INTO clinic (name, address_line1, city, state, postal_code)
    VALUES
      ('Downtown Health Center',        '100 Main St',     'Springfield', 'IL', '62701'),
      ('Northside Family Clinic',       '245 Oak Avenue',  'Madison',     'IL', '53703'),
      ('Riverside Medical Group',       '77 River Rd',     'Portland',    'IL', '97201'),
      ('Lakeside Wellness & Care',      '900 Lake Blvd',   'Minneapolis', 'IL', '55401'),
      ('Southpoint Primary Care',       '55 Elm Street',   'Austin',      'IL', '78701'),
      ('Green Valley Health',           '1200 Greenway Dr','Chicago',     'IL', '60601'),
      ('Harborview Clinic',             '402 Harbor St',   'Rockford',    'IL', '61101'),
      ('Midtown Pediatrics',            '88 Center Plaza', 'Naperville',  'IL', '60540'),
      ('Summit Family Practice',        '200 Summit Ave',  'Champaign',   'IL', '61820'),
      ('Harmony Care Center',           '77 Oakwood Lane', 'Peoria',      'IL', '61602');

    -- 2) Providers
    WITH c AS (
      SELECT id, name, ROW_NUMBER() OVER () as clinic_num FROM clinic
    ),
    specialties AS (
      SELECT specialty, ROW_NUMBER() OVER () as spec_num FROM (
        SELECT unnest(ARRAY[
          'Internal Medicine','Family Medicine','Pediatrics','Dermatology',
          'Obstetrics & Gynecology','Cardiology','Orthopedics','Psychiatry'
        ]) AS specialty
      ) s
    ),
    first_names AS (
      SELECT first_name, ROW_NUMBER() OVER () as fn_num FROM (
        SELECT unnest(ARRAY[
          'Alex','Jordan','Taylor','Morgan','Casey','Riley','Sam','Jamie','Avery','Quinn',
          'Blake','Cameron','Drew','Emery','Finley','Harper','Hayden','Kai','Logan','Parker',
          'Reese','Sage','Skyler','River','Phoenix','Rowan','Sage','Sydney','Tate','Vale'
        ]) AS first_name
      ) f
    ),
    last_names AS (
      SELECT last_name, ROW_NUMBER() OVER () as ln_num FROM (
        SELECT unnest(ARRAY[
          'Johnson','Smith','Lee','Garcia','Brown','Martinez','Davis','Miller','Lopez','Wilson',
          'Anderson','Thompson','White','Harris','Martin','Jackson','Clark','Rodriguez','Lewis','Walker',
          'Hall','Allen','Young','Hernandez','King','Wright','Hill','Scott','Green','Adams',
          'Baker','Gonzalez','Nelson','Carter','Mitchell','Perez','Roberts','Turner','Phillips','Campbell'
        ]) AS last_name
      ) l
    ),
    provider_series AS (
      SELECT generate_series(1, 50) as prov_num
    ),
    unique_providers AS (
      SELECT DISTINCT ON (fn.first_name || ' ' || ln.last_name)
        c.id as clinic_id,
        fn.first_name || ' ' || ln.last_name AS full_name,
        sp.specialty,
        ps.prov_num
      FROM provider_series ps
      JOIN c ON c.clinic_num = ((ps.prov_num - 1) % (SELECT COUNT(*) FROM clinic)) + 1
      JOIN first_names fn ON fn.fn_num = ((ps.prov_num - 1) % (SELECT COUNT(*) FROM first_names)) + 1
      JOIN last_names ln ON ln.ln_num = ((ps.prov_num * 7 - 1) % (SELECT COUNT(*) FROM last_names)) + 1
      JOIN specialties sp ON sp.spec_num = ((ps.prov_num - 1) % (SELECT COUNT(*) FROM specialties)) + 1
      ORDER BY fn.first_name || ' ' || ln.last_name, ps.prov_num
    )
    INSERT INTO provider (clinic_id, full_name, specialty)
    SELECT clinic_id, full_name, specialty
    FROM unique_providers;

    -- 3) Patients (500) — varied names per row (no cartesian joins, no random() reuse)
    WITH series AS (
      SELECT generate_series(1, 500) AS s
    ),
    pools AS (
      SELECT
        ARRAY[
            'Olivia','Liam','Emma','Noah','Amelia','Oliver','Ava','Elijah','Sophia','Mateo',
            'Isabella','Lucas','Mia','Levi','Charlotte','Benjamin','Luna','Ezra','Evelyn','Logan',
            'Giulia','Enzo','Marina','Heitor','Valentina','Gael','Heloisa','Davi','Antonella','Theo',
            'Henry','James','William','Alexander','Michael','Daniel','Jacob','Sebastian','Hugo','Sara',
            'Chloe','Zoe','Nora','Stella','Maya','Muhammad','Aisha','Ibrahim','Aria','Kian',
            'Harper','Ethan','Ella','Mason','Sofia','Diego','Ana','Juan','Lucia','Paolo',
            'Marco','Yuki','Hana','Mei','Chen','Amir','Fatima','Omar','Lea','Victor',
            'Santiago','Camila','Luca','Nina','Ivy','Rafael','Noemi','Kaito','Zara','Rosa'
             ] AS fnames,
             ARRAY[
            'Silva','Santos','Oliveira','Souza','Rodrigues','Ferreira','Almeida','Mendes','Castro','Gomes',
            'Pereira','Carvalho','Lima','Araujo','Teixeira','Ribeiro','Barbosa','Monteiro','Rocha','Cavalcanti',
            'Costa','Nascimento','Moraes','Freitas','Andrade','Cardoso','Nunes','Pinto','Ramos','Dias',
            'Sousa','Barros','Martins','Campos','Correia','Moreira','Bittencourt','Vieira','Duarte','Fonseca',
            'Ribeiro','Siqueira','Pacheco','Teodoro','Barbieri','Bernardes','Figueiredo','Goncalves','Moraes','Cunha',
            'Silveira','Magalhaes','Rezende','Ferraz','Serra','Leite','Ramos','Cordeiro','Alves','Matos'
             ] AS lnames
    )
    INSERT INTO patient (full_name, phone, date_of_birth, email)
    SELECT
      -- Pick name by hashing/indexing with s (spreads nicely and is deterministic)
      pools.fnames[1 + ((s * 37) % cardinality(pools.fnames))] || ' ' ||
      pools.lnames[1 + ((s * 53) % cardinality(pools.lnames))]                                    AS full_name,
      '+1555' || lpad((1000000 + s)::text, 7, '0')                                                AS phone,
      (
        now()::date
        - make_interval(years => 18 + ((s * 29) % 63))  -- 18..80 years
        - ((s * 97) % 365) * INTERVAL '1 day'
      )::date                                                                                     AS date_of_birth,
      'user' || s || '@example.com'                                                               AS email
    FROM series
    CROSS JOIN pools
    -- Optional extra safety if you ever re-run:
    ON CONFLICT (phone) DO NOTHING;

    -- 4) Appointments - Ensure every patient has at least 3 appointments
    DO $inner$
    DECLARE
      r_patient    RECORD;
      r_provider   RECORD;
      i            INT;
      start_ts     TIMESTAMPTZ;
      dur_mins     INT;
      reason_txt   TEXT;
      status_txt   TEXT;
      c_id         UUID;
      p_id         UUID;
      prov_id      UUID;
      base_day     DATE;
    BEGIN
      -- First, ensure every patient gets exactly 3 appointments
      FOR r_patient IN SELECT id FROM patient LOOP
        FOR i IN 1..3 LOOP
          base_day := (now()::date + ((-15 + floor(random()*46))::int));
          start_ts := (base_day::timestamp)
                      + ((9 + floor(random()*9))::int) * INTERVAL '1 hour';
          dur_mins := (ARRAY[30,45,60])[1 + floor(random()*3)];
          reason_txt := (ARRAY['Checkup','Follow-up','Consultation','Therapy'])[1 + floor(random()*4)];
          status_txt := (ARRAY['scheduled','confirmed'])[1 + floor(random()*2)];
          -- Randomly select a clinic and provider
          SELECT id INTO c_id FROM clinic ORDER BY random() LIMIT 1;
          SELECT id INTO prov_id FROM provider ORDER BY random() LIMIT 1;
          INSERT INTO appointment (
            patient_id, clinic_id, provider_id, starts_at, ends_at, reason, status
          )
          VALUES (
            r_patient.id,
            c_id,
            prov_id,
            start_ts,
            start_ts + make_interval(mins => dur_mins),
            reason_txt,
            status_txt
          );
        END LOOP;
      END LOOP;
      
      -- Then add additional random appointments for variety (about 2 more per provider)
      FOR r_provider IN SELECT pr.id FROM provider pr LOOP
        FOR i IN 1..2 LOOP
          base_day := (now()::date + ((-15 + floor(random()*46))::int));
          start_ts := (base_day::timestamp)
                      + ((9 + floor(random()*9))::int) * INTERVAL '1 hour';
          dur_mins := (ARRAY[30,45,60])[1 + floor(random()*3)];
          reason_txt := (ARRAY['Checkup','Follow-up','Consultation','Therapy'])[1 + floor(random()*4)];
          status_txt := (ARRAY['scheduled','confirmed'])[1 + floor(random()*2)];
          -- Randomly select patient and clinic
          SELECT id INTO p_id FROM patient ORDER BY random() LIMIT 1;
          SELECT id INTO c_id FROM clinic ORDER BY random() LIMIT 1;
          INSERT INTO appointment (
            patient_id, clinic_id, provider_id, starts_at, ends_at, reason, status
          )
          VALUES (
            p_id,
            c_id,
            r_provider.id,
            start_ts,
            start_ts + make_interval(mins => dur_mins),
            reason_txt,
            status_txt
          );
        END LOOP;
      END LOOP;
    END $inner$;

  END IF;
END $$;
