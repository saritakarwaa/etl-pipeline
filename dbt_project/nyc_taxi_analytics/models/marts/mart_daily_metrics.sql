-- MART: Daily business KPIs joined with weather
-- This is what the dashboard queries.

WITH trips AS (
    SELECT * FROM {{ ref('stg_taxi_trips') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather') }}
),

daily AS (
    SELECT
        pickup_date,

        -- Volume
        COUNT(*)                                   AS total_trips,
        SUM(passenger_count)                       AS total_passengers,

        -- Revenue
        ROUND(SUM(total_amount), 2)                AS total_revenue,
        ROUND(AVG(total_amount), 2)                AS avg_fare,
        ROUND(AVG(tip_pct), 1)                     AS avg_tip_pct,

        -- Trip quality
        ROUND(AVG(trip_distance_miles), 2)         AS avg_distance_miles,
        ROUND(AVG(trip_duration_minutes), 1)       AS avg_duration_min,
        ROUND(AVG(avg_speed_mph), 1)               AS avg_speed_mph,

        -- Payment mix
        ROUND(
            SUM(CASE WHEN payment_method = 'Credit card' THEN 1 ELSE 0 END)
            * 100.0 / COUNT(*), 1
        )                                          AS pct_card_payments,

        -- Demand by time of day
        SUM(CASE WHEN time_of_day = 'Morning rush' THEN 1 ELSE 0 END)   AS morning_rush_trips,
        SUM(CASE WHEN time_of_day = 'Evening rush' THEN 1 ELSE 0 END)   AS evening_rush_trips,
        SUM(CASE WHEN time_of_day = 'Night'        THEN 1 ELSE 0 END)   AS night_trips

    FROM trips
    GROUP BY pickup_date
)

SELECT
    d.*,
    w.temp_avg_c,
    w.temp_max_c,
    w.temp_min_c,
    w.precipitation_mm,
    w.wind_speed_kmh,
    w.weather_label,
    w.is_bad_weather_day,

    -- Interesting derived insight: does rain increase revenue?
    CASE
        WHEN w.is_bad_weather_day THEN d.total_revenue
        ELSE NULL
    END                                            AS bad_weather_revenue

FROM daily d
LEFT JOIN weather w ON d.pickup_date = w.weather_date
ORDER BY pickup_date
