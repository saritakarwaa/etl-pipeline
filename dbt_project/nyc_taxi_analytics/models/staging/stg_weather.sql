WITH source AS (
    SELECT * FROM {{ source('raw', 'weather') }}
)

SELECT
    CAST(date AS DATE)                               AS weather_date,
    ROUND(temp_max_c, 1)                             AS temp_max_c,
    ROUND(temp_min_c, 1)                             AS temp_min_c,
    ROUND((temp_max_c + temp_min_c) / 2.0, 1)       AS temp_avg_c,
    ROUND(precipitation, 2)                          AS precipitation_mm,
    ROUND(wind_speed, 1)                             AS wind_speed_kmh,
    weather_label,

    -- Classify "bad weather" days for analysis
    CASE
        WHEN precipitation > 5 OR weather_label = 'Snowy' THEN TRUE
        ELSE FALSE
    END                                              AS is_bad_weather_day

FROM source
