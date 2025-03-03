import boto3
import json
import requests
import pandas as pd
from datetime import datetime, timedelta

# S3 clients for both buckets
s3_keys = boto3.client('s3')  # For API keys
s3_data = boto3.client('s3')  # For data

KEY_BUCKET = "your api key bucket"
DATA_BUCKET = "your storage bucket"

def fetch_api_key_from_s3(file_key="apikeys.json"):
    response = s3_keys.get_object(Bucket=KEY_BUCKET, Key=file_key)
    return json.loads(response['Body'].read().decode('utf-8'))['polygon_api_key']

def fetch_last_run():
    try:
        response = s3_data.get_object(Bucket=DATA_BUCKET, Key="btc/last_run.txt")
        last_date = response['Body'].read().decode('utf-8').strip()
        return datetime.strptime(last_date, '%Y-%m-%d')
    except s3_data.exceptions.NoSuchKey:
        return datetime(2025, 10, 1)  # Initial load fallback

def fetch_btc_data(api_key, start_date, end_date):
    url = f'https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/{start_date}/{end_date}'
    response = requests.get(url, params={'apiKey': api_key})
    if response.status_code == 200:
        return response.json()['results']
    print(f"Error: {response.status_code}")
    return []

def append_to_s3(data, prefix="btc"):
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
    df = df[['timestamp', 'o', 'c', 'h', 'l', 'v']]
    df.columns = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
    latest_date = df['Date'].max().strftime('%Y-%m-%d')  # Use latest data date
    local_filename = f"btc_data_{latest_date}.csv"
    s3_key = f"{prefix}/btc_data_{latest_date}.csv"
    df.to_csv(local_filename, index=False)
    s3_data.upload_file(local_filename, DATA_BUCKET, s3_key)
    print(f"Uploaded {s3_key} to S3")
    s3_data.put_object(Bucket=DATA_BUCKET, Key=f"{prefix}/last_run.txt", Body=latest_date)

def main():
    api_key = fetch_api_key_from_s3()
    last_run = fetch_last_run()
    start_date = (last_run + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    if start_date <= end_date:
        data = fetch_btc_data(api_key, start_date, end_date)
        if data:
            append_to_s3(data)
        else:
            print("No new data.")
    else:
        print("Up to date.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")