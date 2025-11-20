# Integrating YARS with Your Stock Agent

This guide shows how to integrate YARS Reddit scraper with your AI stock market agent at:
https://github.com/Viper5579/stock-agent-test

---

## Quick Integration Steps

### 1. Clone YARS to Your Local Machine

```bash
cd ~/Projects  # or wherever you keep your repos
git clone https://github.com/datavorous/YARS.git yars-stockagent
cd yars-stockagent
pip3 install uv  # if not already installed
```

Test it works:
```bash
uv run example/stock_sentiment_scraper.py
```

### 2. Set Up Rotating Proxies

**Option A: Quick Start with Webshare (Cheapest)**

1. Sign up at https://www.webshare.io
2. Get 10 proxies for $2.99/month
3. Set environment variable:

```bash
# Add to your ~/.zshrc or ~/.bash_profile
export REDDIT_PROXY='http://username:password@proxy.webshare.io:80'
```

**Option B: Production Ready with Smartproxy (Recommended)**

1. Sign up at https://smartproxy.com
2. Get residential proxies (~$75/month for 5GB)
3. Set environment variable:

```bash
export REDDIT_PROXY='http://user:pass@gate.smartproxy.com:7000'
```

**See [MAC_QUICKSTART.md](MAC_QUICKSTART.md) for more proxy options**

### 3. Create Reddit Data Module in Your Stock Agent

In your `stock-agent-test` repo, create a new module:

```bash
cd ~/Projects/stock-agent-test  # your stock agent repo
mkdir -p data_sources
touch data_sources/__init__.py
touch data_sources/reddit_data.py
```

### 4. Add Reddit Data Source

Create `data_sources/reddit_data.py`:

```python
"""
Reddit Data Source for Stock Agent
Integrates YARS for sentiment analysis
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import time
import random

# Path to YARS installation
YARS_PATH = str(Path.home() / "Projects" / "yars-stockagent" / "src")
sys.path.insert(0, YARS_PATH)

from yars.yars import YARS


class RedditSentimentDataSource:
    """Fetch and process Reddit data for stock sentiment analysis"""

    def __init__(self, proxy=None):
        """
        Initialize Reddit data source

        Args:
            proxy: Proxy URL or None to use REDDIT_PROXY env var
        """
        if proxy is None:
            proxy = os.getenv('REDDIT_PROXY')

        if not proxy:
            print("⚠️  WARNING: No proxy configured!")
            print("   Set REDDIT_PROXY env var to avoid IP bans")
            print("   export REDDIT_PROXY='http://user:pass@proxy:port'")

        self.miner = YARS(proxy=proxy, timeout=15, random_user_agent=True)

        # Subreddits to monitor
        self.subreddits = [
            "wallstreetbets",
            "stocks",
            "investing",
            "stockmarket",
            "options"
        ]

    def get_ticker_sentiment(self, ticker, limit=20):
        """
        Get sentiment data for a specific stock ticker

        Args:
            ticker: Stock symbol (e.g., "TSLA")
            limit: Max posts per subreddit

        Returns:
            dict: Sentiment data including posts and scores
        """
        print(f"📊 Fetching Reddit sentiment for {ticker}...")

        data = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "posts": [],
            "total_mentions": 0,
            "avg_score": 0,
            "avg_comments": 0
        }

        all_posts = []

        for sub in self.subreddits:
            try:
                posts = self.miner.search_subreddit(
                    sub,
                    ticker,
                    limit=limit,
                    sort="relevance"
                )

                if posts:
                    print(f"  ✓ r/{sub}: {len(posts)} posts")
                    all_posts.extend(posts)

                # Rate limiting
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                print(f"  ✗ r/{sub}: {e}")
                continue

        if all_posts:
            data["posts"] = all_posts
            data["total_mentions"] = len(all_posts)

        return data

    def get_trending_stocks(self, subreddit="wallstreetbets", limit=50):
        """
        Get trending posts from stock subreddit

        Args:
            subreddit: Subreddit to scrape
            limit: Number of posts

        Returns:
            list: Hot posts with metadata
        """
        print(f"🔥 Fetching trending posts from r/{subreddit}...")

        try:
            posts = self.miner.fetch_subreddit_posts(
                subreddit,
                limit=limit,
                category="hot",
                time_filter="day"
            )
            print(f"  ✓ Retrieved {len(posts)} posts")
            return posts

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return []

    def get_detailed_sentiment(self, permalink):
        """
        Get full post with comments for deep sentiment analysis

        Args:
            permalink: Reddit post permalink

        Returns:
            dict: Post with all comments
        """
        try:
            details = self.miner.scrape_post_details(permalink)
            return details
        except Exception as e:
            print(f"  ✗ Error getting post details: {e}")
            return None

    def extract_tickers_from_posts(self, posts, known_tickers=None):
        """
        Extract stock tickers mentioned in posts

        Args:
            posts: List of post dictionaries
            known_tickers: Set of known ticker symbols to look for

        Returns:
            dict: Ticker mention counts
        """
        if known_tickers is None:
            # Common tickers (you should expand this)
            known_tickers = {
                "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN",
                "META", "AMD", "NFLX", "DIS", "GME", "AMC",
                "SPY", "QQQ", "VOO"
            }

        ticker_counts = {}

        for post in posts:
            title = post.get('title', '').upper()
            description = post.get('description', '').upper()

            for ticker in known_tickers:
                # Look for ticker in title or description
                if ticker in title or ticker in description:
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        return dict(sorted(ticker_counts.items(),
                          key=lambda x: x[1],
                          reverse=True))


# Example Usage
if __name__ == "__main__":
    # Initialize data source
    reddit = RedditSentimentDataSource()

    # Example 1: Get sentiment for specific tickers
    watchlist = ["TSLA", "NVDA", "AAPL"]

    for ticker in watchlist:
        sentiment = reddit.get_ticker_sentiment(ticker, limit=10)
        print(f"\n{ticker}: {sentiment['total_mentions']} mentions")
        time.sleep(3)  # Rate limiting

    # Example 2: Get trending posts and extract tickers
    trending = reddit.get_trending_stocks("wallstreetbets", limit=30)

    if trending:
        print(f"\nFound {len(trending)} trending posts")
        ticker_mentions = reddit.extract_tickers_from_posts(trending)

        print("\nMost mentioned tickers:")
        for ticker, count in list(ticker_mentions.items())[:10]:
            print(f"  {ticker}: {count} mentions")

    # Example 3: Deep analysis of top post
    if trending:
        top_post = trending[0]
        print(f"\nAnalyzing: {top_post['title']}")
        details = reddit.get_detailed_sentiment(top_post['permalink'])

        if details:
            print(f"  Comments: {len(details.get('comments', []))}")
```

### 5. Use in Your Stock Agent

In your main agent code:

```python
from data_sources.reddit_data import RedditSentimentDataSource

# Initialize
reddit = RedditSentimentDataSource()

# Get sentiment for your watchlist
watchlist = ["TSLA", "NVDA", "AAPL", "AMD", "MSFT"]
sentiment_data = {}

for ticker in watchlist:
    sentiment_data[ticker] = reddit.get_ticker_sentiment(ticker, limit=15)

# Use this data in your trading logic
for ticker, data in sentiment_data.items():
    mentions = data['total_mentions']

    # Your logic here
    if mentions > 50:
        print(f"{ticker} is trending on Reddit! {mentions} mentions")
        # Maybe this signals increased volatility or sentiment shift
```

---

## Architecture Suggestions

### Recommended Project Structure

```
stock-agent-test/
├── data_sources/
│   ├── __init__.py
│   ├── reddit_data.py          # YARS integration
│   ├── news_data.py             # News APIs
│   └── market_data.py           # Price/volume data
├── sentiment/
│   ├── __init__.py
│   ├── reddit_sentiment.py     # Analyze Reddit data
│   └── ml_models.py             # Your ML models
├── trading/
│   ├── __init__.py
│   ├── strategy.py              # Trading strategies
│   └── execution.py             # Order execution
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── config.py
├── data/                        # Store scraped data
│   └── reddit/
├── main.py
└── requirements.txt
```

### Data Flow

```
1. [Reddit] → YARS → reddit_data.py → Raw posts/comments
                          ↓
2. Raw data → sentiment_analysis.py → Sentiment scores
                          ↓
3. Sentiment scores + Market data → strategy.py → Trading signals
                          ↓
4. Trading signals → execution.py → Orders
```

---

## Automated Data Collection

### Set Up Cron Job for Continuous Monitoring

Create `scripts/collect_reddit_data.py`:

```python
#!/usr/bin/env python3
"""
Automated Reddit data collection for stock agent
Run this via cron for continuous monitoring
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add your stock agent to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.reddit_data import RedditSentimentDataSource


def main():
    reddit = RedditSentimentDataSource()

    # Your watchlist (could load from config file)
    watchlist = [
        "TSLA", "AAPL", "NVDA", "AMD", "MSFT",
        "GOOGL", "META", "AMZN", "NFLX"
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "tickers": {}
    }

    # Collect sentiment for each ticker
    for ticker in watchlist:
        try:
            data = reddit.get_ticker_sentiment(ticker, limit=10)
            results["tickers"][ticker] = data
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    # Save to data directory
    data_dir = PROJECT_ROOT / "data" / "reddit"
    data_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = data_dir / f"sentiment_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Data saved to {filename}")


if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x scripts/collect_reddit_data.py
```

### Add to Crontab

```bash
crontab -e
```

Add these lines:

```bash
# Collect Reddit sentiment every 4 hours during trading week
0 6,10,14,18 * * 1-5 cd ~/Projects/stock-agent-test && /usr/local/bin/python3 scripts/collect_reddit_data.py

# Collect at market open (9:30 AM EST = 14:30 UTC)
30 14 * * 1-5 cd ~/Projects/stock-agent-test && /usr/local/bin/python3 scripts/collect_reddit_data.py
```

---

## Sentiment Analysis Integration

### Basic Sentiment Scorer

Create `sentiment/reddit_sentiment.py`:

```python
"""
Simple sentiment analysis for Reddit posts
You can integrate more sophisticated NLP models later
"""

from collections import Counter
import re


class RedditSentimentAnalyzer:
    """Basic sentiment analysis for Reddit stock discussions"""

    def __init__(self):
        # Simple keyword-based sentiment
        # You should expand this or use ML models
        self.bullish_keywords = {
            'moon', 'calls', 'buy', 'long', 'bullish', 'rocket',
            'tendies', 'gain', 'profit', 'up', 'pump', 'hold'
        }

        self.bearish_keywords = {
            'puts', 'sell', 'short', 'bearish', 'crash', 'dump',
            'loss', 'down', 'overvalued', 'bubble', 'tank'
        }

    def analyze_post(self, post):
        """
        Analyze sentiment of a single post

        Args:
            post: Dictionary with 'title' and 'description'

        Returns:
            dict: Sentiment scores
        """
        text = f"{post.get('title', '')} {post.get('description', '')}".lower()

        bullish_count = sum(1 for word in self.bullish_keywords if word in text)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text)

        # Simple sentiment score
        if bullish_count > bearish_count:
            sentiment = "bullish"
            confidence = bullish_count / (bullish_count + bearish_count + 1)
        elif bearish_count > bullish_count:
            sentiment = "bearish"
            confidence = bearish_count / (bullish_count + bearish_count + 1)
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count
        }

    def analyze_posts(self, posts):
        """Analyze multiple posts and aggregate sentiment"""
        sentiments = [self.analyze_post(post) for post in posts]

        bullish = sum(1 for s in sentiments if s['sentiment'] == 'bullish')
        bearish = sum(1 for s in sentiments if s['sentiment'] == 'bearish')
        neutral = sum(1 for s in sentiments if s['sentiment'] == 'neutral')

        total = len(sentiments)

        return {
            "total_posts": total,
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "bullish_ratio": bullish / total if total > 0 else 0,
            "bearish_ratio": bearish / total if total > 0 else 0,
            "overall_sentiment": "bullish" if bullish > bearish else
                                 "bearish" if bearish > bullish else "neutral"
        }


# Usage
if __name__ == "__main__":
    from data_sources.reddit_data import RedditSentimentDataSource

    reddit = RedditSentimentDataSource()
    analyzer = RedditSentimentAnalyzer()

    # Get posts for a ticker
    ticker = "TSLA"
    data = reddit.get_ticker_sentiment(ticker, limit=20)

    # Analyze sentiment
    sentiment = analyzer.analyze_posts(data['posts'])

    print(f"\nSentiment Analysis for {ticker}:")
    print(f"  Total posts: {sentiment['total_posts']}")
    print(f"  Bullish: {sentiment['bullish']} ({sentiment['bullish_ratio']:.1%})")
    print(f"  Bearish: {sentiment['bearish']} ({sentiment['bearish_ratio']:.1%})")
    print(f"  Overall: {sentiment['overall_sentiment'].upper()}")
```

---

## Testing Your Integration

### Test Script

Create `tests/test_reddit_integration.py`:

```python
"""Test Reddit data integration"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.reddit_data import RedditSentimentDataSource
from sentiment.reddit_sentiment import RedditSentimentAnalyzer


def test_reddit_connection():
    """Test basic Reddit scraping"""
    print("Testing Reddit connection...")

    reddit = RedditSentimentDataSource()

    # Test 1: Get trending posts
    print("\n[Test 1] Fetching trending posts...")
    trending = reddit.get_trending_stocks("wallstreetbets", limit=5)
    assert len(trending) > 0, "No posts retrieved"
    print(f"✓ Retrieved {len(trending)} posts")

    # Test 2: Get ticker sentiment
    print("\n[Test 2] Fetching ticker sentiment...")
    sentiment = reddit.get_ticker_sentiment("TSLA", limit=5)
    print(f"✓ Found {sentiment['total_mentions']} mentions")

    # Test 3: Sentiment analysis
    print("\n[Test 3] Analyzing sentiment...")
    analyzer = RedditSentimentAnalyzer()
    if sentiment['posts']:
        analysis = analyzer.analyze_posts(sentiment['posts'])
        print(f"✓ Sentiment: {analysis['overall_sentiment']}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_reddit_connection()
```

Run it:
```bash
python3 tests/test_reddit_integration.py
```

---

## Production Deployment

### Environment Variables

Create `.env` file in your stock-agent-test repo:

```bash
# Reddit scraping
REDDIT_PROXY=http://username:password@proxy.example.com:8000

# Optional: Multiple proxies for rotation
REDDIT_PROXY_1=http://proxy1:8000
REDDIT_PROXY_2=http://proxy2:8000
REDDIT_PROXY_3=http://proxy3:8000

# Rate limiting
REDDIT_MIN_DELAY=2
REDDIT_MAX_DELAY=5

# Subreddits to monitor
REDDIT_SUBREDDITS=wallstreetbets,stocks,investing,stockmarket

# Stock watchlist
STOCK_WATCHLIST=TSLA,NVDA,AAPL,AMD,MSFT,GOOGL,META
```

Load with python-dotenv:
```bash
pip3 install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

proxy = os.getenv('REDDIT_PROXY')
```

### Docker Deployment (Optional)

If you want to containerize:

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy YARS
COPY yars-stockagent/ /app/yars/

# Copy your agent
COPY stock-agent-test/ /app/agent/

# Install dependencies
RUN cd /app/yars && uv sync
RUN cd /app/agent && uv sync

CMD ["python3", "/app/agent/main.py"]
```

---

## Next Steps

1. **Set up proxy** → Start with Webshare ($2.99/month)
2. **Test integration** → Run test script
3. **Collect data** → Run collection script manually
4. **Analyze sentiment** → Integrate with your trading logic
5. **Automate** → Set up cron jobs
6. **Monitor** → Log scraping results and errors
7. **Scale** → Add more proxies and subreddits

---

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'yars'"**

Fix the path in `reddit_data.py`:
```python
YARS_PATH = str(Path.home() / "Projects" / "yars-stockagent" / "src")
```

**Issue: Rate limiting / 429 errors**

Increase delays:
```python
time.sleep(random.uniform(5, 10))  # Longer delays
```

**Issue: IP banned despite using proxy**

- Verify proxy is working: `curl -x $REDDIT_PROXY https://reddit.com`
- Switch to residential proxies (datacenter IPs get banned easier)
- Rotate proxies more frequently

---

## Resources

- **YARS Documentation**: [MAC_QUICKSTART.md](MAC_QUICKSTART.md)
- **Your Stock Agent**: https://github.com/Viper5579/stock-agent-test
- **Reddit API Status**: https://www.redditstatus.com
- **Best Practices**: Always respect rate limits and Reddit's ToS

---

**Happy scraping! 📈**
