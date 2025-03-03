Python 3.12.8

# Capstone 2025: Not Financial Advice (Trust Score)
https://www.mermaidchart.com/app/projects/dbef8be6-c2c3-4ce5-adbe-bb9e960a437e/diagrams/6d2c5cb3-0e4c-4e86-9483-078110701093/version/v0.1/edit

https://www.mermaidchart.com/raw/6d2c5cb3-0e4c-4e86-9483-078110701093?theme=light&version=v0.1&format=svg

## Overview
This document outlines the data ingestion and processing pipeline for the Trust Score project, focusing on integrating financial data from Polygon (BTC prices) and X ( influencer sentiment), leveraging Large Language Models (LLMs) for sentiment analysis, storing data in Amazon S3, and loading it into Snowflake for analytics. The pipeline ensures fresh, structured data for Bitcoin (BTC) price predictions and influencer recommendations, supporting downstream transformations and visualizations.

## Pipeline Architecture

### 1. Data Sources
- **Polygon (BTC Price Data)**:
  - Fetches historical and real-time Bitcoin price data from the Polygon API, focusing on price, volume, and market metrics from February 24, 2025, onward.
  - Data is filtered for relevance (e.g., daily OHLCV—Open, High, Low, Close, Volume) and stored temporarily for processing.

- **X (Influencer Sentiment)**:
  - Collects posts from five key Bitcoin influencers (e.g., TheMoonCarl, WhalePanda, AshCrypto, CoinTelegraph, BitcoinMagazine) from February 21 to February 27, 2025, for bulk loading, with daily increments planned.
  - Filters posts for BTC-related keywords (e.g., "Bitcoin", "BTC", "#Bitcoin", "#BTC"), excludes retweets, and captures metadata (timestamp, likes, retweets, language).

### 2. Data Processing
- **Polygon Data Processing**:
  - Transforms Polygon API responses into a structured format (e.g., CSV with columns: timestamp, price, volume).
  - Validates data for completeness and consistency, handling missing values or outliers.

- **X Data Processing with LLM**:
  - Preprocesses X posts by removing URLs and special characters for cleaner input.
  - Uses a Large Language Model (via LangChain and OpenAI) to score each post's sentiment on a 1–10 scale, where:
    - 1–4 indicates a sell recommendation for Bitcoin (1 = strongest sell, 4 = mild sell).
    - 5–6 indicates neutral sentiment (rare, no clear buy/sell intent).
    - 7–10 indicates a buy recommendation for Bitcoin (7 = mild buy, 10 = strongest buy).
  - Groups tweets by influencer and date, aggregating text for scoring accuracy.

### 3. Data Storage (Amazon S3)
- **Storage Location**:
  - Data is saved as CSV files in an Amazon S3 bucket (e.g., `data-bucket/tweets/` for X, `data-bucket/btc/` for Polygon).
  - Files are named `analyzed_tweets_<date>.csv` (X) or `btc_prices_<date>.csv` (Polygon), created daily or in bulk, ensuring no overwriting.

- **Upload Process**:
  - Uses `boto3` to upload processed DataFrames (Pandas) to S3, triggering notifications for downstream ingestion.
  - Ensures data integrity with local temporary files (`/tmp/`) before S3 transfer.

### 4. Data Ingestion (Snowflake)
- **Snowflake Setup**:
  - Utilizes Snowflake’s Snowpipe for automated ingestion from S3, triggered by S3 event notifications.
  - Data lands in raw staging tables (e.g., `trust_score.raw.staging_data`) and is split/transformed by a Snowflake task into `trust_score.raw.analyzed_tweets` (X) and `trust_score.raw.btc_prices` (Polygon).

- **Pipeline Configuration**:
  - **Snowpipe**: Configured with a notification integration (e.g., `s3_notification`) to monitor the S3 bucket for new `.csv` files.
  - **Task**: Runs `split_data_task` periodically to move data from staging to raw tables, deduplicating and validating timestamps.
  - **Storage Integration**: Links S3 to Snowflake, ensuring secure access with AWS credentials.

### 5. Pipeline Flow
- **Polygon → S3 → Snowflake**:
  1. Fetch BTC prices from Polygon API.
  2. Process and save to S3 (`btc_prices_<date>.csv`).
  3. Snowpipe ingests into `trust_score.raw.btc_prices`, task transforms for analytics.

- **X → LLM → S3 → Snowflake**:
  1. Fetch tweets from X API for 5 influencers.
  2. Preprocess, score with LLM (1–10), and save to S3 (`analyzed_tweets_<date>.csv`).
  3. Snowpipe ingests into `trust_score.raw.analyzed_tweets`, task transforms for analytics.

### 6. Credit and Rate Limit Management
- **X API (Twitter)**:
  - Operates under a Basic tier (15,000 posts/month).
  - Caps bulk load at 1,470 posts (Feb 21–27), daily increments at 50 posts/day (5 influencers × 10 tweets/day).
  - Limits API calls to 300 requests/15 min, using 1 retry with 15-min delays to avoid rate limits.

- **Polygon API**:
  - Assumes a similar credit system—monitors usage to stay within limits, typically lower volume than X.

### 7. Automation and Scheduling
- **Airflow**:
  - Deploys pipelines via Docker containers, using `combined_dag.py` to orchestrate Polygon and X data fetches daily.
  - Schedules bulk backfills (e.g., Feb 21–27) and incremental updates (e.g., Mar 1 onward) on `@daily` intervals.

- **Astronomer**:
  - Plans to deploy to Astronomer for cloud orchestration, ensuring scalability and monitoring.

## Technical Details
- **Languages/Tools**:
  - Python (Tweepy for X, `boto3` for S3, Pandas for data manipulation, LangChain/OpenAI for LLMs).
  - Snowflake (Snowpipe, tasks, storage integrations).
  - Amazon S3 (storage, event notifications).
  - Docker/Airflow (local testing, cloud deployment).

- **Dependencies**:
  - `requirements_data_ingestion.txt`: Includes `tweepy`, `boto3`, `pandas`, `langchain-openai`, `openai`.

- **Error Handling**:
  - Handles X API rate limits, S3 upload failures, LLM scoring errors, and Snowflake ingestion issues with retries and logging.

## Status and Next Steps
- **Current Status (Feb 28, 2025)**:
  - Polygon pipeline complete (fully working from Feb 24 onward).
  - X pipeline bulk load in progress (Feb 21–27, targeting 1,470 posts), incremental setup planned for Mar 1.

- **Next Steps**:
  - Complete X bulk load (Feb 21–27).
  - Build and test incremental X pipeline (Mar 1 onward, 50 posts/day).
  - Commit to GitHub, secure API keys, deploy to Astronomer, and start Pipeline 2 (dbt transformations, visualization).

Trust Score Pipeline]
  ├── [Data Sources]
  │   ├── [Polygon (BTC Prices)]
  │   │   └── Fetches BTC price, volume, metrics (Feb 24 onward)
  │   └── [X (Twitter Influencers)]
  │       └── Fetches tweets for 5 influencers (Feb 21–27, increments Mar 1 onward)
  │
  ├── [Data Processing]
  │   ├── [Polygon Processing]
  │   │   └── Transforms to CSV (timestamp, price, volume), validates data
  │   └── [X Processing with LLM]
  │       ├── Preprocesses tweets (removes URLs)
  │       └── Scores sentiment (1–10) via OpenAI, groups by influencer/date
  │
  ├── [Data Storage (S3)]
  │   ├── [Polygon Data]
  │   │   └── Saves to `data-bucket/btc/btc_prices_<date>.csv`
  │   └── [X Data]
  │       └── Saves to `data-bucket/tweets/analyzed_tweets_<date>.csv`
  │
  └── [Data Ingestion (Snowflake)]
      ├── [Snowpipe]
      │   ├── Monitors S3 for new `.csv` files
      │   └── Ingests to `trust_score.raw.staging_data`
      └── [Snowflake Task]
          └── Transforms to `trust_score.raw.btc_prices` and `trust_score.raw.analyzed_tweets`

[Automation]
  ├── [Airflow]
  │   └── Orchestrates daily fetches via Docker, schedules bulk/incremental runs
  └── [Astronomer]
      └── Deploys to cloud for scalability

[Credit Management]
  ├── [X API]
  │   └── Limits to 15,000 posts/month, caps bulk at 1,470, increments at 50/day
  └── [Polygon API]
      └── Monitors usage, stays within limits

## Contributors
- Anastasia Simpson

