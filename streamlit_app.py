import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
from cryptography.hazmat.primitives import serialization  # Required for key deserialization
from cryptography.hazmat.backends import default_backend  # Required for backend

# Sidebar styling (X-inspired design)
st.sidebar.title("Filters")
st.markdown("""
<style>
    .stMultiSelect [data-baseweb="select"] {
        background-color: #1A1A1A !important;
        border: 2px solid #1DA1F2 !important;
        color: #FFFF00 !important;
        font-weight: bold !important;
    }
    .stMultiSelect [data-baseweb="select"] option {
        background-color: #1A1A1A !important;
        color: #FFFF00 !important;
    }
    .main {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
    }
    .stPlotlyChart {
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    .stDataFrame {
        background-color: #2D2D2D !important;
        border-radius: 10px !important;
    }
    .stDataFrame th {
        background-color: #1DA1F2 !important;
        color: #FFFFFF !important;
    }
    .tweet-card {
        background-color: #2D2D2D !important;
        border-radius: 10px !important;
        padding: 10px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    .tweet-username {
        color: #1DA1F2 !important;
        font-weight: bold !important;
    }
    .tweet-score {
        color: #FF6B6B !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# Filters
date_range = st.sidebar.date_input("Select Date Range", [pd.to_datetime('2025-01-01'), pd.to_datetime('2025-02-27')])
influencers = st.sidebar.multiselect("Select Influencers", 
                                    options=['BitcoinMagazine', 'TheMoonCarl', 'WhalePanda', 'CoinTelegraph'], 
                                    default=['BitcoinMagazine', 'TheMoonCarl', 'WhalePanda', 'CoinTelegraph'])

# Snowflake connection (updated without passphrase)
private_key_pem = st.secrets["snowflake"]["private_key_file_content"].encode()

# Deserialize the unencrypted private key
private_key = serialization.load_pem_private_key(
    private_key_pem,
    password=None,  # No passphrase since it’s unencrypted
    backend=default_backend()
)

# Convert to DER format for Snowflake
private_key_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Snowflake connection using secrets
private_key_content = st.secrets["snowflake"]["private_key_file_content"].encode()
conn = snowflake.connector.connect(
    account=st.secrets["snowflake"]["account"],
    user=st.secrets["snowflake"]["user"],
    private_key=private_key_content,
    role=st.secrets["snowflake"]["role"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"],
    warehouse=st.secrets["snowflake"]["warehouse"]
)

# Visualization 1: Influencer Accuracy Leaderboard
st.subheader("Influencer Accuracy Leaderboard")
leaderboard_query = f"""
SELECT
    USERNAME,
    COUNT(*) AS total_recommendations,
    SUM(CASE WHEN IS_INFLUENCER_CORRECT_DAILY = TRUE THEN 1 ELSE 0 END) AS correct_recommendations,
    (SUM(CASE WHEN IS_INFLUENCER_CORRECT_DAILY = TRUE THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS accuracy_percentage
FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS
WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
    {'AND USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
GROUP BY USERNAME
ORDER BY accuracy_percentage DESC
"""
leaderboard_df = pd.read_sql(leaderboard_query, conn)

if leaderboard_df.empty:
    st.error("No leaderboard data.")
else:
    leaderboard_df = leaderboard_df.rename(columns={'USERNAME': 'USERNAME'})
    st.dataframe(leaderboard_df.style.format({'accuracy_percentage': '{:.2f}%'}), 
                 use_container_width=True, height=400)

# Visualization 2: Influencer Recommendation Accuracy Heatmap
st.subheader("Influencer Recommendation Accuracy vs. Bitcoin Price Trends")
heatmap_query = f"""
SELECT 
    tsa.DATE,
    tsa.USERNAME,
    tsa.IS_INFLUENCER_CORRECT_DAILY,
    ba.CLOSE
FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS tsa
LEFT JOIN TRUST_SCORE.raw_ANALYTICS.BTC_ANALYTICS ba
    ON tsa.DATE = ba.DATE
WHERE tsa.DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}' 
    {'AND tsa.USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
"""
heatmap_df = pd.read_sql(heatmap_query, conn)

if heatmap_df.empty:
    st.error("No heatmap data.")
else:
    heatmap_df = heatmap_df.rename(columns={'DATE': 'DATE', 'USERNAME': 'USERNAME', 
                                           'IS_INFLUENCER_CORRECT_DAILY': 'correctness', 'CLOSE': 'btc_price'})
    heatmap_df['DATE'] = pd.to_datetime(heatmap_df['DATE'], errors='coerce')
    heatmap_df['btc_price'] = pd.to_numeric(heatmap_df['btc_price'], errors='coerce')
    heatmap_df['correctness'] = heatmap_df['correctness'].map({True: 1, False: 0})
    heatmap_df = heatmap_df.dropna(subset=['DATE', 'USERNAME', 'correctness'])

    heatmap_df = heatmap_df.groupby(['USERNAME', 'DATE']).agg({
        'correctness': 'mean',
        'btc_price': 'first'
    }).reset_index()

    pivot = heatmap_df.pivot(index='USERNAME', columns='DATE', values='correctness')
    btc_prices = heatmap_df[['DATE', 'btc_price']].drop_duplicates().sort_values('DATE')

    fig_heatmap = make_subplots(specs=[[{"secondary_y": True}]])
    fig_heatmap.add_trace(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, 
                                    colorscale=[[0, 'red'], [1, 'green']], 
                                    colorbar=dict(title="Correctness", tickvals=[0, 1], ticktext=["No", "Yes"])), 
                          secondary_y=False)
    fig_heatmap.add_trace(go.Scatter(x=btc_prices['DATE'], y=btc_prices['btc_price'], mode='lines', 
                                    name='BTC Price', line=dict(color='#1DA1F2')), 
                          secondary_y=True)
    fig_heatmap.update_layout(
        plot_bgcolor='#1A1A1A',
        paper_bgcolor='#1A1A1A',
        font=dict(color='#FFFFFF'),
        xaxis=dict(showgrid=False, title='Date'),
        yaxis=dict(showgrid=False, title='Influencer'),
        yaxis2=dict(showgrid=False, title='Price ($)', side='right', overlaying='y'),
        height=400,
        width=1500,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# Visualization 3: Extreme Sentiment Tweets (Hardcoded with Two Tweets)
st.subheader("Extreme Sentiment Tweets")
st.markdown(f"""
<div class="tweet-card">
    <span class="tweet-username">TheMoonCarl</span> - 2025-02-26<br>
    <p>The last time the RSI was this low, #Bitcoin pumped by 120%!<br>
    This time BTC will go even higher!<br>
    BTCwillgoevenhigher!BTC at $1 is undervalued<br>
    BTCat10k is still undervalued<br>
    BTCat100k is the beginning<br>
    BTCat500k is still just the beginning<br>
    BTCat1m is the breakout<br>
    BTCat5m is the momentum shrift<br>
    BTCat10m is the super cycle<br>
    BTCat20m+is the mainstream…<br>
    BTCisformingthissymmetricaltriangleonsmallertimeframes.Bearish−85,800🎯 Bullish - 92,250🎯<br>
    Trade #Bitcoin on Bitunix - and get a free 100afteryourfirst500 deposit!<br>
    Should I take $50 million of my Bitcoin and dump it into altcoins? 🤔<br>
    Buy Bitcoin today, thank me in 3 months.</p>
    <span class="tweet-score">Sentiment Score: 10.0</span>
</div>
<div class="tweet-card">
    <span class="tweet-username">TheMoonCarl</span> - 2025-02-21<br>
    <p>Bitcoin will 5x<br>
    Ethereum will 9x<br>
    Altcoins will 200x<br>
    Be prepared.<br>
    This year. Sell your meme coin now, buy Bitcoin.<br>
    Thank me in 6 months. BITCOIN TRADE:</p>
    <span class="tweet-score">Sentiment Score: 10.0</span>
</div>
""", unsafe_allow_html=True)

# Visualization 4: Bitcoin Daily
st.subheader("Bitcoin Daily")
btc_query_daily = f"""
SELECT DATE, CLOSE
FROM TRUST_SCORE.raw_ANALYTICS.BTC_ANALYTICS
WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
ORDER BY DATE
"""
btc_daily_df = pd.read_sql(btc_query_daily, conn)

if btc_daily_df.empty:
    st.error("No daily Bitcoin data.")
else:
    btc_daily_df = btc_daily_df.rename(columns={'CLOSE': 'daily_price', 'DATE': 'DATE'})
    btc_daily_df['DATE'] = pd.to_datetime(btc_daily_df['DATE'], errors='coerce')
    btc_daily_df['daily_price'] = pd.to_numeric(btc_daily_df['daily_price'], errors='coerce')
    btc_daily_df = btc_daily_df.dropna(subset=['DATE', 'daily_price'])

    fig_daily = px.line(btc_daily_df, x='DATE', y='daily_price', title="Bitcoin Daily Price Trend 📈",
                        line_shape='linear', color_discrete_sequence=['#1DA1F2'])
    fig_daily.update_layout(
        plot_bgcolor='#1A1A1A',
        paper_bgcolor='#1A1A1A',
        font=dict(color='#FFFFFF'),
        xaxis=dict(showgrid=False, title='Date'),
        yaxis=dict(showgrid=False, title='Price ($)'),
        height=400,
        width=1500,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    st.plotly_chart(fig_daily, use_container_width=True)

# Visualization 5: Bitcoin Weekly (Fixed)
# st.subheader("Bitcoin Weekly")
# btc_query_weekly = f"""
# SELECT DATE_TRUNC('week', DATE) AS week_start, AVG(CLOSE) AS weekly_price
# FROM TRUST_SCORE.raw_ANALYTICS.BTC_ANALYTICS
# WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
# GROUP BY DATE_TRUNC('week', DATE)
# ORDER BY week_start
# """
# btc_weekly_df = pd.read_sql(btc_query_weekly, conn)

# if btc_weekly_df.empty:
#     st.error("No weekly Bitcoin data.")
# else:
#     btc_weekly_df['week_start'] = pd.to_datetime(btc_weekly_df['week_start'], errors='coerce')
#     btc_weekly_df['weekly_price'] = pd.to_numeric(btc_weekly_df['weekly_price'], errors='coerce')
#     btc_weekly_df = btc_weekly_df.dropna(subset=['week_start', 'weekly_price'])

#     fig_weekly = px.line(btc_weekly_df, x='week_start', y='weekly_price', title="Bitcoin Weekly Price Trend 📈",
#                          line_shape='linear', color_discrete_sequence=['#1DA1F2'])
#     fig_weekly.update_layout(
#         plot_bgcolor='#1A1A1A',
#         paper_bgcolor='#1A1A1A',
#         font=dict(color='#FFFFFF'),
#         xaxis=dict(showgrid=False, title='Week Start'),
#         yaxis=dict(showgrid=False, title='Price ($)'),
#         height=400,
#         width=1500,
#         margin=dict(l=10, r=10, t=40, b=20)
#     )
#     st.plotly_chart(fig_weekly, use_container_width=True)

# Visualization 6: Daily Influencer Sentiment Scores (Fixed Indentation)
st.subheader("Daily Influencer Sentiment Scores")
sentiment_query = f"""
SELECT 
    USERNAME,
    DATE,
    SENTIMENT_SCORE
FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS
WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}' 
    {'AND USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
ORDER BY DATE, USERNAME
"""
sentiment_df = pd.read_sql(sentiment_query, conn)

if sentiment_df.empty:
    st.error("No sentiment data.")
else:
    sentiment_df = sentiment_df.rename(columns={'DATE': 'DATE', 'USERNAME': 'USERNAME', 'SENTIMENT_SCORE': 'sentiment_score'})
    sentiment_df['DATE'] = pd.to_datetime(sentiment_df['DATE'], errors='coerce')
    sentiment_df['sentiment_score'] = pd.to_numeric(sentiment_df['sentiment_score'], errors='coerce')
    sentiment_df = sentiment_df.dropna(subset=['DATE', 'sentiment_score'])

    for username in influencers:
        user_df = sentiment_df[sentiment_df['USERNAME'] == username].sort_values('DATE')
        if not user_df.empty:
            fig_sentiment = px.bar(user_df, x='DATE', y='sentiment_score', 
                                   title=f"{username} Daily Sentiment 📊",
                                   color_discrete_sequence=['#FF6B6B'])
            fig_sentiment.update_layout(
                plot_bgcolor='#1A1A1A',
                paper_bgcolor='#1A1A1A',
                font=dict(color='#FFFFFF'),
                xaxis=dict(showgrid=False, title='Date'),
                yaxis=dict(showgrid=False, title='Sentiment Score (1-10)'),
                height=400,
                width=1500,
                margin=dict(l=10, r=10, t=40, b=20)
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)

# Visualization 7: Influencer Correctness Ratio
st.subheader("Influencer Correctness Ratio")
ratio_query = f"""
WITH active_days AS (
    SELECT USERNAME, TO_DATE(DATE) AS DATE
    FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS
    WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
    {'AND USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
    GROUP BY USERNAME, TO_DATE(DATE)
),
recommendations AS (
    SELECT USERNAME, DATE, IS_INFLUENCER_CORRECT_DAILY
    FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS
    WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
    {'AND USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
)
SELECT
    r.USERNAME,
    COUNT(DISTINCT a.DATE) AS total_active_days,
    SUM(CASE WHEN r.IS_INFLUENCER_CORRECT_DAILY = TRUE THEN 1 ELSE 0 END) AS correct_days,
    (SUM(CASE WHEN r.IS_INFLUENCER_CORRECT_DAILY = TRUE THEN 1 ELSE 0 END) / COUNT(DISTINCT a.DATE)) * 100 AS correct_ratio
FROM recommendations r
JOIN active_days a ON r.USERNAME = a.USERNAME AND r.DATE = a.DATE
GROUP BY r.USERNAME
ORDER BY correct_ratio DESC
"""
ratio_df = pd.read_sql(ratio_query, conn)

if ratio_df.empty:
    st.error("No correctness ratio data.")
else:
    ratio_df = ratio_df.rename(columns={'USERNAME': 'USERNAME'})
    st.dataframe(ratio_df.style.format({'correct_ratio': '{:.2f}%'}), 
                 use_container_width=True, height=400)

# Visualization 8: Bitcoin Price vs. Sentiment Trends
# st.subheader("Bitcoin Price vs. Sentiment Trends")
# btc_query = f"""
# SELECT DATE, CLOSE
# FROM TRUST_SCORE.raw_ANALYTICS.BTC_ANALYTICS
# WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}'
# """
# sentiment_trend_query = f"""
# SELECT DATE, AVG(SENTIMENT_SCORE) AS avg_sentiment
# FROM TRUST_SCORE.raw_ANALYTICS.TRUST_SCORE_ANALYTICS
# WHERE DATE BETWEEN '{date_range[0].strftime('%Y-%m-%d')}' AND '{date_range[1].strftime('%Y-%m-%d')}' 
#     {'AND USERNAME IN (' + ','.join(f"'{i}'" for i in influencers) + ')' if influencers else ''}
# GROUP BY DATE
# ORDER BY DATE
# """
# btc_df = pd.read_sql(btc_query, conn)
# sentiment_trend_df = pd.read_sql(sentiment_trend_query, conn)

# if btc_df.empty or sentiment_trend_df.empty:
#     st.error("No data for price vs. sentiment trends.")
# else:
#     btc_df['DATE'] = pd.to_datetime(btc_df['DATE'], errors='coerce')
#     btc_df['CLOSE'] = pd.to_numeric(btc_df['CLOSE'], errors='coerce')
#     sentiment_trend_df['DATE'] = pd.to_datetime(sentiment_trend_df['DATE'], errors='coerce')
#     sentiment_trend_df['avg_sentiment'] = pd.to_numeric(sentiment_trend_df['avg_sentiment'], errors='coerce')
#     btc_df = btc_df.dropna(subset=['DATE', 'CLOSE'])
#     sentiment_trend_df = sentiment_trend_df.dropna(subset=['DATE', 'avg_sentiment'])

#     fig_trends = go.Figure()
#     fig_trends.add_trace(go.Scatter(x=btc_df['DATE'], y=btc_df['CLOSE'], mode='lines', name='Bitcoin Price ($)', 
#                                     line=dict(color='#1DA1F2'), yaxis='y2'))
#     fig_trends.add_trace(go.Scatter(x=sentiment_trend_df['DATE'], y=sentiment_trend_df['avg_sentiment'], mode='lines', 
#                                     name='Avg Sentiment', line=dict(color='#FF6B6B')))
#     fig_trends.update_layout(
#         plot_bgcolor='#1A1A1A',
#         paper_bgcolor='#1A1A1A',
#         font=dict(color='#FFFFFF'),
#         xaxis=dict(showgrid=False, title='Date'),
#         yaxis=dict(showgrid=False, title='Sentiment Score'),
#         yaxis2=dict(showgrid=False, title='Price ($)', side='right', overlaying='y'),
#         height=400,
#         width=1500,
#         margin=dict(l=10, r=10, t=40, b=20)
#     )
#     st.plotly_chart(fig_trends, use_container_width=True)

conn.close()