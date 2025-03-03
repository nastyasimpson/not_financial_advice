import pandas as pd
import boto3
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

# Securely set up OpenAI API Key
api_key = "you api key"

# Initialize OpenAI LLM via LangChain
llm = OpenAI(temperature=0.0, openai_api_key=api_key)

# Define the sentiment analysis prompt template
prompt_template = PromptTemplate(
    input_variables=["post"],
    template="""
    You are a financial sentiment expert specializing in Bitcoin trading signals. 
    You will be presented with a tweet and must determine whether the text implies 
    a recommendation to buy or sell Bitcoin.

    Your output should be a single number between -1 and 1, with no additional text. All values between -1 and +1 are allowed.
    Return only a numerical score between -1 and +1 (e.g., "0.5"), nothing else.

    - -1 indicates the strongest recommendation to sell Bitcoin.
    - +1 indicates the strongest recommendation to buy Bitcoin.
    - 0 indicates a completely neutral sentiment.

    Provide your output based solely on the information within the tweet: {text}
    """
)

# Create a RunnableSequence
chain = prompt_template | llm  # Simplified syntax for RunnableSequence

# Function to analyze text using LangChain and OpenAI
def analyze_recommendation_with_openai(text: str) -> float:
    try:
        result = chain.invoke({"text":text})
        score = float(result.strip())  # Convert the output to a float
        return max(min(score, 1.0), -1.0)  # Ensure score stays within [-1, 1]
    except ValueError:
        print(f"Could not convert '{result}' to float for text: {text}")
        return 0.0  # Neutral if conversion fails
    except Exception as e:
        print(f"Error processing text: {text}. Error: {e}")
        return 0.0

# Read the CSV file
df = pd.read_csv('themooncarl_tweets_since_2025-02-01.csv')
df = df[['Username', 'Timestamp', 'Text']]
df['post'] = df['Text']


# Check if 'text' column exists
if 'Text' not in df.columns:
    raise ValueError("The CSV must contain a 'text' column.")

# Apply the sentiment analysis
df['influencer_not_financial_advice'] = df['post'].apply(analyze_recommendation_with_openai)

# Save to S3 bucket
# s3_client = boto3.client('s3')
# bucket_name = 'your-bucket-name'
# file_key = 'your-folder-path/analyzed_tweets.csv'

# Save DataFrame to a local CSV first
local_file = 'analyzed_tweets.csv'
df.to_csv(local_file, index=False)

# Upload to S3
# s3_client.upload_file(local_file, bucket_name, file_key)
# print(f"Analysis complete. DataFrame with new column saved to s3://{bucket_name}/{file_key}")


