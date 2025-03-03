import tweepy
import boto3
import pandas as pd
import json
import time
import re  # For link removal
from datetime import datetime, timezone, timedelta
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate

# AWS S3 setup
DATA_BUCKET = "your_bucket"  # Data bucket (tweets, BTC)
KEY_BUCKET = "you api keys bucke, JSON"  # API keys bucket
API_KEY_FILE = "apikeys.json"

s3_keys = boto3.client('s3')
s3_data = boto3.client('s3')

def get_api_keys(bucket_name, object_key="apikeys.json"):
    try:
        response = s3_keys.get_object(Bucket=bucket_name, Key=object_key)
        keys = json.loads(response["Body"].read().decode("utf-8"))
        return {
            "x_api_key": keys.get("X_API_Key"),
            "x_api_secret": keys.get("X_API_Key_Secret"),
            "x_bearer_token": keys.get("X_Bearer_Token"),
            "openai_api_key": keys.get("openai_api_key")
        }
    except Exception as e:
        print(f"Error retrieving API keys from S3: {e}")
        return None

api_keys = get_api_keys(KEY_BUCKET)
if not api_keys:
    print("Failed to retrieve API keys from S3. Using hardcoded fallback for testing (fix today).")
    # Hardcoded fallback for today’s test—remove for production
    api_keys = {
        "x_api_key": None,  # X API key not needed with bearer token
        "x_api_secret": None,  # X API secret not needed with bearer token
        "x_bearer_token": None,  # Assume X bearer token is in environment or handled elsewhere
        "openai_api_key": "enter your key"
    }
    if not api_keys["openai_api_key"]:
        print("Failed to set OpenAI API key. Exiting.")
        exit(1)

# Tweepy Auth
client = tweepy.Client(
    bearer_token=api_keys["x_bearer_token"],
    wait_on_rate_limit=True
)

# LLM Setup
llm = OpenAI(temperature=0.0, openai_api_key=api_keys["openai_api_key"])



prompt_template = PromptTemplate(
    input_variables=["text"],
    template="""
    You are a financial sentiment expert specializing in Bitcoin trading signals. 
    You will be presented with tweets (concatenated if multiple) and must determine the overall recommendation to buy or sell Bitcoin.

    Your output should be a single integer between 1 and 10, with no additional text. All values between 1 and 10 are allowed.
    Return only a numerical score between 1 and 10 (e.g., "8"), nothing else.

    - 1-4 indicates a recommendation to sell Bitcoin (1 = strongest sell, 4 = mild sell).
    - 5-6 indicates a neutral sentiment (rare, only if no clear buy/sell intent).
    - 7-10 indicates a recommendation to buy Bitcoin (7 = mild buy, 10 = strongest buy).

    Consider negations (e.g., 'DO NOT SELL' implies buy). Provide your output based solely on the information within the tweets, focusing on the influencer's intent: {text}
    """
)

# Tweet Analyzer
chain = prompt_template | llm

def analyze_recommendation_with_openai(text):
    try:
        result = chain.invoke({"text": text})
        score = int(float(result.strip()))
        return max(min(score, 10), 1)
    except ValueError:
        print(f"Could not convert '{result}' to int for text: {text}")
        return 5  # Neutral if fails
    except Exception as e:
        print(f"Error processing text: {text}. Error: {e}")
        return 5

INFLUENCERS = ["TheMoonCarl", "WhalePanda", "AshCrypto", "CoinTelegraph", "BitcoinMagazine"]  # example influencers

def fetch_tweets(influencers, start_time=None, end_time=None, max_results=50, max_retries=1, current=None, start=None, incremental=False):
    all_tweets = []
    api_calls = 0
    retry_count = 0

    for influencer in influencers:
        try:
            user = client.get_user(username=influencer)
            if not user.data:
                print(f"User {influencer} not found. Skipping...")
                continue
            user_id = user.data.id

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    tweets = client.get_users_tweets(
                        id=user_id,
                        tweet_fields=["created_at", "public_metrics", "text", "lang", "author_id"],
                        exclude=["retweets"],
                        start_time=start_time.isoformat() if start_time else None,
                        end_time=end_time.isoformat() if end_time else None,
                        max_results=max_results if not incremental else 10  # 50 for bulk, 10 for incremental (50 posts/day total)
                    )
                    api_calls += max_results if not incremental else 10  # Adjust calls for incremental
                    if tweets.data:
                        daily_tweets = [
                            {
                                "Username": influencer,
                                "Timestamp": tweet.created_at,
                                "Text": re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet.text),
                                "Likes": tweet.public_metrics["like_count"],
                                "Retweets": tweet.public_metrics["retweet_count"],
                                "Language": tweet.lang,
                                "id": tweet.id
                            }
                            for tweet in tweets.data
                            if tweet.text.lower().count("btc") + tweet.text.lower().count("bitcoin") + tweet.text.lower().count("#btc") + tweet.text.lower().count("#bitcoin") > 0
                        ]
                        # Soft daily cap: 20 posts/day for bulk (1,400 total), 10 posts/day for incremental (50 total)
                        daily_cap = 20 if not incremental else 10  # 5 influencers × 4 tweets/day (bulk), 5 × 2 (incremental)
                        if current and start:
                            if len(all_tweets) + len(daily_tweets) <= daily_cap * (current - start).days + daily_cap:
                                all_tweets.extend(daily_tweets[:daily_cap - len(all_tweets) % daily_cap])  # Limit per day
                        else:
                            all_tweets.extend(daily_tweets)  # Fallback if current/start not provided (for testing)
                    break  # Success, exit loop
                except tweepy.TooManyRequests:
                    if retry_count < max_retries:
                        print(f"Rate limit for {influencer}. Waiting 15 minutes... (Retry {retry_count + 1}/{max_retries})")
                        time.sleep(900)  # Wait full 15 minutes
                        retry_count += 1
                        continue  # Retry once
                    else:
                        print(f"Rate limit exceeded for {influencer} after {max_retries} retries. Skipping to save credits...")
                        break  # Skip, don’t waste credits
                except tweepy.TweepyException as e:
                    print(f"Error fetching {influencer}: {e}")
                    break
        except Exception as e:
            print(f"Unexpected error for {influencer}: {e}")
            continue
    print(f"API calls this run: {api_calls}")
    # Credit safety check—stop if nearing 90% of 15,000 (13,500)
    if api_calls >= 13500:
        print("WARNING: Approaching X API credit limit (13,500/15,000 posts). Stopping to preserve credits...")
        return []
    # Total caps: 1,400 for bulk, 50 for incremental (daily)
    if not incremental:
        if len(all_tweets) > 1400:  # Bulk cap for Feb 4–20
            all_tweets = all_tweets[:1400]  # Limit to 1,400 total posts
    else:
        if len(all_tweets) > 50:  # Incremental daily cap
            all_tweets = all_tweets[:50]  # Limit to 50 posts/day
    return all_tweets

def merge_and_score(tweets):
    if not tweets:
        return pd.DataFrame()
    df = pd.DataFrame(tweets)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    grouped = df.groupby(['Username', df['Timestamp'].dt.date])['Text'].agg('\n'.join).reset_index()
    grouped['post'] = grouped['Text']
    grouped['influencer_not_financial_advice'] = grouped['post'].apply(analyze_recommendation_with_openai)
    return grouped[['Username', 'Timestamp', 'Text', 'post', 'influencer_not_financial_advice']]

def append_to_s3(df, prefix="tweets", date_str=None):
    if not df.empty:
        if not date_str:
            date_str = df['Timestamp'].dt.date.min().strftime('%Y-%m-%d')
        local_file = f"/tmp/analyzed_tweets_{date_str}.csv"
        df.to_csv(local_file, index=False)
        s3_key = f"{prefix}/analyzed_tweets_{date_str}.csv"
        s3_data.upload_file(local_file, DATA_BUCKET, s3_key)
        print(f"Uploaded {s3_key} to S3")

def main(bulk=True, incremental=False, date=None):
    if bulk:
        # Bulk load Feb 4–20 for 5 influencers (skip Feb 1–3, already processed)
        start = datetime(2025, 2, 4, tzinfo=timezone.utc)  # Skip Feb 1–3, already processed
        end = datetime(2025, 2, 21, tzinfo=timezone.utc)  # Excludes Feb 21
        current = start
        total_calls = 0
        while current < end:
            next_day = current + timedelta(days=1)
            tweets = fetch_tweets(INFLUENCERS, start_time=current, end_time=next_day, max_results=50, current=current, start=start, incremental=False)
            if tweets:
                df = merge_and_score(tweets)
                append_to_s3(df, date_str=current.strftime('%Y-%m-%d'))
            total_calls += len(INFLUENCERS) * 50  # 5 influencers × 50 tweets max/day
            current = next_day
            time.sleep(15)  # Wait 15 seconds between days to avoid rate limits, maximize speed
    elif incremental and date:
        # Incremental load for a specific day (from date parameter, e.g., yesterday)
        if isinstance(date, str):
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                print(f"Invalid date format: {date}. Expected 'YYYY-MM-DD'. Using today as fallback.")
                date_obj = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            date_obj = date.replace(tzinfo=timezone.utc) if date else datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start = date_obj
        end = start + timedelta(days=1)
        tweets = fetch_tweets(INFLUENCERS, start_time=start, end_time=end, max_results=10, current=start, start=start, incremental=True)
        if tweets:
            df = merge_and_score(tweets)
            append_to_s3(df, date_str=start.strftime('%Y-%m-%d'))
        print(f"API calls this run: {len(INFLUENCERS) * 10}")  # 5 influencers × 10 tweets max/day
    else:
        print("No logic specified—use bulk=True or incremental=True with date.")

if __name__ == "__main__":
    # For bulk load (run manually for Feb 4–20)
    # print("Running fast bulk load for 5 influencers from February 4–20, 2025...")
    # main(bulk=True)

    # For incremental (to be used in Airflow DAG, Mar 1 onward)
    from datetime import date
    yesterday = date.today() - timedelta(days=1)
    print(f"Running incremental load for {yesterday}...")
    main(incremental=True, date=yesterday.strftime('%Y-%m-%d'))