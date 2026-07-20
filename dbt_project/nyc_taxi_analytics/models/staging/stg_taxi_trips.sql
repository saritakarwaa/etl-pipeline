-- Staging model: clean and standardise raw taxi data
-- Materialized as VIEW (no storage cost, always fresh)

WITH source AS (
    SELECT * FROM {{ source('raw', 'taxi_trips') }}
),

cleaned AS (
    SELECT
        -- ── Time dimensions ──────────────────────────
        tpep_pickup_datetime                             AS pickup_at,
        tpep_dropoff_datetime                            AS dropoff_at,
        DATE(tpep_pickup_datetime)                       AS pickup_date,
        HOUR(tpep_pickup_datetime)                       AS pickup_hour,
        DAYOFWEEK(tpep_pickup_datetime)                  AS day_of_week,  -- 1=Sun

        -- ── Trip details ──────────────────────────────
        passenger_count,
        ROUND(trip_distance, 2)                          AS trip_distance_miles,

        -- ── Duration (derived) ───────────────────────
        ROUND(
            DATEDIFF('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0,
            2
        )                                                AS trip_duration_minutes,

        -- ── Financials ────────────────────────────────
        ROUND(fare_amount, 2)                            AS fare_amount,
        ROUND(tip_amount, 2)                             AS tip_amount,
        ROUND(total_amount, 2)                           AS total_amount,

        -- ── Derived metrics ───────────────────────────
        ROUND(tip_amount / NULLIF(fare_amount, 0) * 100, 1)
                                                         AS tip_pct,

        ROUND(trip_distance / NULLIF(
            DATEDIFF('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 3600.0,
        0), 1)                                           AS avg_speed_mph,

        -- ── Payment method (decoded) ──────────────────
        CASE payment_type
            WHEN 1 THEN 'Credit card'
            WHEN 2 THEN 'Cash'
            WHEN 3 THEN 'No charge'
            WHEN 4 THEN 'Dispute'
            ELSE 'Unknown'
        END                                              AS payment_method,

        -- ── Time of day buckets ───────────────────────
        CASE
            WHEN HOUR(tpep_pickup_datetime) BETWEEN 6  AND 9  THEN 'Morning rush'
            WHEN HOUR(tpep_pickup_datetime) BETWEEN 10 AND 15 THEN 'Midday'
            WHEN HOUR(tpep_pickup_datetime) BETWEEN 16 AND 19 THEN 'Evening rush'
            WHEN HOUR(tpep_pickup_datetime) BETWEEN 20 AND 23 THEN 'Night'
            ELSE 'Late night'
        END                                              AS time_of_day

    FROM source

    -- ── Remove clear outliers ─────────────────────────
    WHERE fare_amount     BETWEEN 2.50 AND 500
      AND trip_distance   BETWEEN 0.1  AND 100
      AND trip_duration_minutes BETWEEN 1 AND 240
      AND passenger_count BETWEEN 1    AND 6
)

SELECT * FROM cleaned
