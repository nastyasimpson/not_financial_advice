{{ config(materialized='table', schema='ANALYTICS') }}

WITH btc_data AS (
    SELECT * FROM {{ ref('btc_analytics') }}
),
tweets_data AS (
    SELECT * FROM {{ ref('tweets_analytics') }}
),
joined_data AS (
    SELECT
        t.USERNAME,
        t.DATE,
        t.POST,
        t.sentiment_score,
        b.CLOSE,
        b.daily_pct_change,
        b.weekly_pct_change,
        b.did_btc_increase_daily,
        b.did_btc_increase_weekly,
        -- Interpret sentiment score, preserving NULL for missing values
        CASE 
            WHEN t.sentiment_score IS NULL THEN NULL
            WHEN t.sentiment_score BETWEEN 1 AND 4 THEN 'Sell'
            WHEN t.sentiment_score BETWEEN 5 AND 6 THEN 'Neutral'
            WHEN t.sentiment_score BETWEEN 7 AND 10 THEN 'Buy'
            ELSE 'Unknown'
        END AS sentiment_direction,
        -- Check if influencer was "correct," handling NULL sentiment as not applicable (FALSE)
        CASE 
            WHEN t.sentiment_score IS NULL THEN FALSE
            WHEN t.sentiment_score BETWEEN 7 AND 10 AND b.did_btc_increase_daily THEN TRUE
            WHEN t.sentiment_score BETWEEN 1 AND 4 AND NOT b.did_btc_increase_daily THEN TRUE
            ELSE FALSE
        END AS is_influencer_correct_daily,
        CASE 
            WHEN t.sentiment_score IS NULL THEN FALSE
            WHEN t.sentiment_score BETWEEN 7 AND 10 AND b.did_btc_increase_weekly THEN TRUE
            WHEN t.sentiment_score BETWEEN 1 AND 4 AND NOT b.did_btc_increase_weekly THEN TRUE
            ELSE FALSE
        END AS is_influencer_correct_weekly,
        -- Data quality flag: only flag missing critical data (e.g., price), not sentiment
        CASE 
            WHEN b.CLOSE IS NULL THEN 'Missing price'
            ELSE 'Complete'
        END AS data_quality_flag
    FROM tweets_data t
    LEFT JOIN btc_data b ON t.DATE = b.DATE
    WHERE t.DATE BETWEEN '2025-01-01' AND '2025-03-01'
)
SELECT
    USERNAME,
    DATE,
    POST,
    sentiment_score,  -- Preserves NULL for missing sentiment, not treated as bad quality
    CLOSE,
    daily_pct_change,
    weekly_pct_change,
    did_btc_increase_daily,
    did_btc_increase_weekly,
    sentiment_direction,
    is_influencer_correct_daily,
    is_influencer_correct_weekly,
    data_quality_flag
FROM joined_data