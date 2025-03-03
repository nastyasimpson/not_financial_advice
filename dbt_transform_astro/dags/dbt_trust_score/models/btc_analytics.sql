{{ config(materialized='table', schema='ANALYTICS') }}

WITH btc_cleaned AS (
    SELECT
        DATE,
        OPEN,
        CLOSE,
        HIGH,
        LOW,
        VOLUME,
        LOAD_TIMESTAMP,
        -- Calculate % difference from previous day's close
        LAG(CLOSE) OVER (ORDER BY DATE) AS prev_day_close,
        CASE 
            WHEN prev_day_close IS NOT NULL 
            THEN ROUND(((CLOSE - prev_day_close) / prev_day_close) * 100, 2)
            ELSE NULL 
        END AS daily_pct_change,
        -- 7-day rolling % change
        LAG(CLOSE, 7) OVER (ORDER BY DATE) AS prev_week_close,
        CASE 
            WHEN prev_week_close IS NOT NULL 
            THEN ROUND(((CLOSE - prev_week_close) / prev_week_close) * 100, 2)
            ELSE NULL 
        END AS weekly_pct_change
    FROM {{ source('raw', 'btc_data') }}
    WHERE DATE IS NOT NULL  -- Basic data quality check
)
SELECT
    DATE,
    OPEN,
    CLOSE,
    HIGH,
    LOW,
    VOLUME,
    LOAD_TIMESTAMP,
    daily_pct_change,
    weekly_pct_change,
    -- Boolean flags for price movement
    CASE WHEN daily_pct_change > 0 THEN TRUE ELSE FALSE END AS did_btc_increase_daily,
    CASE WHEN weekly_pct_change > 0 THEN TRUE ELSE FALSE END AS did_btc_increase_weekly
FROM btc_cleaned