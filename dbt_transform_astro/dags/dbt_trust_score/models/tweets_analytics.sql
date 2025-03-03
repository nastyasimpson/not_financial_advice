{{ config(materialized='table', schema='ANALYTICS') }}

WITH tweets_cleaned AS (
    SELECT
        USERNAME,
        TIMESTAMP,
        POST,
        INFLUENCER_NOT_FINANCIAL_ADVICE AS sentiment_score,
        LOAD_TIMESTAMP,
        -- Extract date from timestamp for joining
        CAST(TIMESTAMP AS DATE) AS tweet_date
    FROM {{ source('raw', 'analyzed_tweets') }}
    WHERE USERNAME IS NOT NULL AND POST IS NOT NULL  -- Basic data quality check
),
-- Add rows for missing days per influencer (Jan 1 - March 1, 2025)
date_spine AS (
    SELECT DATEADD(day, seq4(), '2025-01-01') AS date
    FROM TABLE(GENERATOR(rowcount => 60))  -- 60 days from Jan 1 to March 1
),
influencers AS (
    SELECT DISTINCT USERNAME FROM tweets_cleaned
),
missing_days AS (
    SELECT
        i.USERNAME,
        d.date AS tweet_date,
        'No tweets today' AS POST,
        NULL AS sentiment_score,
        CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
    FROM influencers i
    CROSS JOIN date_spine d
    LEFT JOIN tweets_cleaned t ON i.USERNAME = t.USERNAME AND d.date = t.tweet_date
    WHERE t.USERNAME IS NULL
)
SELECT
    USERNAME,
    tweet_date AS DATE,
    POST,
    sentiment_score,
    LOAD_TIMESTAMP
FROM tweets_cleaned
UNION ALL
SELECT
    USERNAME,
    tweet_date AS DATE,
    POST,
    sentiment_score,
    LOAD_TIMESTAMP
FROM missing_days