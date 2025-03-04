# Not Financial Advice  
**Unveiling Trust in the Chaos of Crypto Predictions**  
*Your Data-Driven Compass for Bitcoin Influencer Credibility*  

Welcome to **Not Financial Advice**, a DataExpert Capstone by Anastasia Simpson designed to bring clarity to the noisy world of cryptocurrency predictions. This project helps users navigate Bitcoin influencer claims with a dynamic **Trust Score**—a metric that highlights who’s worth listening to amid the flood of "not financial advice" chatter.

---

## 🌟 The Vision  
In today’s crypto landscape, X influencers shape Bitcoin sentiment, often with little transparency around their credibility. Our goal? To offer **clear, actionable insight** by scoring influencers on their prediction accuracy and consistency. Whether you’re new to trading or a seasoned investor, this tool helps you figure out: *Who’s signal, and who’s just noise?*

---

## 🚀 What We Do  
- **Capture the Market**: Pulls live and historical Bitcoin data from Polygon API (since Jan 01, 2025).  
- **Decode the Influencers**: Analyzes X posts from top Bitcoin voices (e.g., TheMoonCarl, WhalePanda,BitcoinMagazine, CoinTelegraph) using Langchain/OpenAI LLMs.  
- **Score the Trust**: Builds a **Trust Score** based on prediction accuracy and sentiment reliability.  
- **Visualize the Truth**: Powers an interactive Streamlit app, live on Streamlit Cloud, with clear, actionable insights.  

**Key Callout**: *Our Trust Score isn’t just data—it’s your edge in a volatile market.*

---

## ⚙️ How It Works  
### Pipeline Architecture  
Ambition to build a robust pipeline that turns raw crypto data into actionable insights. 

### Pipeline Breakdown  
- **Polygon API (BTC Prices)** → **Amazon S3**  
  - Fetches real-time Bitcoin price data and stages it securely.  
- **X API (Influencer Posts)** → **LLM Sentiment Scoring using Langchain** → **Amazon S3**  
  - Pulls posts, scores them (1–10: Sell to Buy), and stores the results.  
- **Amazon S3** → **Snowflake (Snowpipe Ingestion)**  
  - Seamlessly ingests data into Snowflake’s cloud warehouse.  
- **Snowflake** → **dbt Transformations**  
  - Refines raw data into analytics-ready tables.  
- **dbt Transformations** → **Streamlit App (Trust Score Dashboard)**  
  - Powers the live, interactive dashboard on Streamlit Cloud.  
- **Airflow (Orchestration)**  
  - Automates and connects the flow, targeting Polygon, X, and dbt steps.  

- **Data Sources**: Polygon for BTC prices, X for influencer sentiment.  
- **Processing**: LLMs score posts (1–10: Sell to Buy), staged in S3.  
- **Storage**: Snowflake with Snowpipe for seamless ingestion.  
- **Transformation**: dbt refines data into analytics-ready tables.  
- **Visualization**: Streamlit Cloud hosts the live dashboard.  

---

## 🎯 Key Features  
- **Dynamic Trust Score**: Reflects prediction accuracy and sentiment trends.  
- **Real-Time Insights**: Daily BTC prices paired with influencer recommendations.  
- **Interactive Dashboard**: Live on [Streamlit Cloud](https://notfinancialadvice.streamlit.app/).  
- **Rock-Solid Data**: dbt enforces rigorous quality checks at every step.

## 🛠️ Tech Stack: The Powerhouse Behind the Project  
We’ve built **Not Financial Advice** on a reliable, scalable stack designed for precision and growth. Here’s how each piece fits:  

| **Component**            | **Tool**             | **Why We Chose It**                                                                 |  
|--------------------------|----------------------|------------------------------------------------------------------------------------|  
| **Data Sources**         | **Polygon API**      | Delivers real-time, reliable BTC price data (OHLCV) with top-tier accuracy.        |  
|                          | **X API + Tweepy**   | Streams influencer posts efficiently, capturing sentiment from the crypto pulse.  |  
| **BUY/SELL 
|  Sentiment Analysis**    | **LangChain + OpenAI**| Powers LLM-driven scoring (1–10) for Buy/Sell intent with sharp precision.       |  
| **Storage & Processing** | **AWS S3 + Boto3**   | Secure, scalable storage for raw and processed data, with tight AWS integration.  |  
|                          | **Snowflake**        | Cloud-native warehouse with Snowpipe for real-time ingestion and Tasks for automation.|  
| **Transformation**       | **dbt**              | Modular SQL transforms raw data into analytics-ready tables, with built-in tests. |  
| **Orchestration**        | **Airflow + Astronomer** | Automates daily pipelines locally (Docker) and scales to the cloud with Astronomer.|  
| **Visualization**        | **Streamlit**        | Builds a clean, interactive dashboard—easy to deploy, intuitive to use.          |  

### Deep Dive: Why This Stack Works  
- **Polygon API**: High-frequency BTC data keeps our price trends fresh and accurate.  
- **Tweepy + X API**: Optimized for 15,000 posts/month, targeting key influencers (e.g., 50 posts/day across 5 voices).  
- **LangChain + OpenAI**: Scores sentiment with a custom prompt, adept at nuances like “DO NOT SELL.”  
- **AWS S3 + Boto3**: Stores CSV files (e.g., `btc_prices_<date>.csv`) securely, triggering Snowflake ingestion via notifications.  
- **Snowflake**: Snowpipe auto-loads data into staging tables, with Tasks splitting it into `trust_score.raw.analyzed_tweets` and `trust_score.raw.btc_prices`.  
- **dbt**: Models like `btc_analytics.sql` and `trust_score_analytics.sql` ensure clean, validated outputs in `TRUST_SCORE.ANALYTICS`.  
- **Airflow + Astronomer**: Runs `combined_dag.py` locally in Docker, with plans for cloud orchestration on Astronomer.  
- **Streamlit**: Deploys a sleek UI with minimal fuss, hosted live for instant access.  

**Bold Claim**: *This stack balances simplicity and power—built to deliver today, ready to scale tomorrow.*
---

### Part 2: Sneak Peek to End
```markdown
---

## 📊 Sneak Peek  
- **Deployed App**: [Live on Streamlit Cloud](https://not-financial-advice.streamlit.app)  
- **GitHub Repo**: [github.com/nastyasimpson/not_financial_advice](https://github.com/nastyasimpson/not_financial_advice)  
- **Screenshots**:  
  ![Astro Deploy](astro_deploy_screenshot.png)  
  ![Local Airflow](airflow_pipeline_screenshot.png)  

---

## 🌍 Impact  
Crypto moves fast, and the noise can be overwhelming. We’re here to **support users**—from casual traders to seasoned investors—with a tool to assess influencer credibility and make informed choices. Whether it’s catching a solid signal or avoiding the hype, **Not Financial Advice** is your guide through the digital currency storm.

---

## 🔮 What’s Next?  
- **Incremental Updates**: Daily influencer pulls (50 posts/day) starting Mar 1, 2025.  
- **Cloud Orchestration**: Full Astronomer deployment for scalability.  
- **Expanded Sources**: YouTube sentiment via transcriptions on the horizon.  
- **Enhanced Validation**: Tighter LLM input checks for sharper accuracy.  

---

## 👩‍💻 Meet the Creator  
**Anastasia Simpson**  
DataExpert Capstone Developer  
Turning raw data into trust, one pipeline at a time.

---

**Not Financial Advice**: *In crypto, trust matters—and we’re here to help you find it.*
