import tweepy
import boto3
import pandas as pd
import json
import time
from datetime import datetime, timezone

# AWS S3 bucket and object details
#locally saved on csv, example data load file, for full code with LLM use fetch_and_analyze_x.py

S3_BUCKET_NAME = "trustscorebtc"  # S3 Bucket name
S3_OBJECT_KEY = "apikeys.json"    # S3 object key (file path)

# Function to retrieve Twitter API credentials from S3
def get_twitter_api_keys(bucket_name, object_key):
    try:
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        keys = json.loads(response["Body"].read().decode("utf-8"))
        return keys
    except Exception as e:
        print(f"Error retrieving API keys from S3: {e}")
        return None

# Retrieve API keys from S3
api_keys = get_twitter_api_keys(S3_BUCKET_NAME, S3_OBJECT_KEY)
if not api_keys:
    print("Failed to retrieve API keys. Exiting.")
    exit(1)

# Twitter API credentials from S3
API_KEY = api_keys["X_API_Key"]
API_SECRET = api_keys["X_API_Key_Secret"]
BEARER_TOKEN = api_keys["X_Bearer_Token"]

# Authenticate with Tweepy
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Influencer's Twitter username
influencer_username = "TheMoonCarl"

# Specify start date
start_date = datetime(2025, 2, 20, tzinfo=timezone.utc)

# Function to fetch tweets
def fetch_tweets(username, max_results=5):
    try:
        # Get the user ID of the influencer
        user = client.get_user(username=username)
        user_id = user.data.id

        # Fetch tweets
        tweets = client.get_users_tweets(
            id=user_id,
            tweet_fields=["created_at", "public_metrics", "text", "lang", "author_id"],
            exclude=["retweets"],  # Exclude retweets
            start_time=start_date.isoformat(),
            max_results=max_results
        )

        if tweets.data:
            return [
                {
                    "Username": username,
                    "Timestamp": tweet.created_at,
                    "Text": tweet.text,
                    "Likes": tweet.public_metrics["like_count"],
                    "Retweets": tweet.public_metrics["retweet_count"],
                    "Language": tweet.lang
                }
                for tweet in tweets.data
                if ("Bitcoin" in tweet.text or "BTC" in tweet.text) and not tweet.text.startswith("RT")  # Filter by keywords and exclude retweets
            ]
        else:
            print(f"No tweets found for {username}.")
            return []
    except tweepy.TooManyRequests:
        print("Rate limit reached. Retrying after 15 minutes...")
        time.sleep(15 * 60)  # Wait for 15 minutes (standard Twitter API reset time)
        return fetch_tweets(username, max_results)
    except Exception as e:
        print(f"Error fetching tweets for {username}: {e}")
        return []

# Main execution
if __name__ == "__main__":
    print(f"Fetching tweets for {influencer_username} since {start_date.date()}...")
    tweets = fetch_tweets(influencer_username, max_results=5)

    # Save tweets to CSV
    if tweets:
        df = pd.DataFrame(tweets)
        filename = f"themooncarl_tweets_since_{start_date.date()}.csv"
        df.to_csv(filename, index=False)
        print(f"Tweets saved to {filename}")
    else:
        print("No tweets to save.")