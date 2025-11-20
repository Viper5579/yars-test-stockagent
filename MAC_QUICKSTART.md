# YARS Mac Quickstart Guide
## For AI Stock Market Investment Agents

This guide will help you set up YARS (Yet Another Reddit Scraper) on Mac for your AI stock market investment agent. Reddit is a valuable source for sentiment analysis, trending stocks discussions, and investment insights.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Rotating Proxies Setup](#rotating-proxies-setup)
- [Integration with AI Stock Agent](#integration-with-ai-stock-agent)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python 3.13+
```bash
brew install python@3.13
```

Verify installation:
```bash
python3 --version
```

### 3. Install Git (if not already installed)
```bash
brew install git
```

---

## Installation

### Step 1: Clone the Repository
```bash
cd ~/Projects  # or your preferred directory
git clone https://github.com/datavorous/YARS.git yars-stockagent
cd yars-stockagent
```

### Step 2: Install UV Package Manager
UV is a fast Python package manager that handles dependencies efficiently.

```bash
pip3 install uv
```

Or using Homebrew:
```bash
brew install uv
```

### Step 3: Test the Installation
Run the example script to verify everything works:

```bash
uv run example/example.py
```

This will:
- Create a virtual environment automatically
- Install all required dependencies (requests, Pygments)
- Run the example scraper

---

## Basic Usage

### Quick Start Example

Create a file called `stock_scraper.py` in your project:

```python
import sys
import os

# Add YARS to path
sys.path.append('src')

from yars.yars import YARS
from yars.utils import display_results

# Initialize without proxy (for testing only - use proxies in production!)
miner = YARS()

# Search for stock-related discussions
stock_results = miner.search_reddit("TSLA stock", limit=10)
print(f"Found {len(stock_results)} posts about TSLA")

# Get posts from WallStreetBets
wsb_posts = miner.fetch_subreddit_posts(
    "wallstreetbets",
    limit=20,
    category="hot",
    time_filter="day"
)

# Get detailed post with comments for sentiment analysis
if wsb_posts:
    permalink = wsb_posts[0]["permalink"]
    post_details = miner.scrape_post_details(permalink)

    # This contains title, body, and all comments - perfect for sentiment analysis
    print(f"Post: {post_details['title']}")
    print(f"Comments: {len(post_details['comments'])}")
```

### Run it:
```bash
uv run stock_scraper.py
```

---

## Rotating Proxies Setup

**IMPORTANT:** Reddit will ban your IP if you scrape without proxies. For production use, rotating proxies are essential.

### Option 1: Free Proxy Lists (Not Recommended for Production)

Free proxies are unreliable but good for testing:

```python
from yars.yars import YARS

# Use a single proxy
proxy = "http://proxy-ip:port"
miner = YARS(proxy=proxy, timeout=15)
```

### Option 2: Paid Rotating Proxy Services (Recommended)

For your AI stock agent, use a reliable proxy service:

#### A. Bright Data (formerly Luminati)
Best for enterprise, reliable, expensive (~$500/month for residential)

```python
from yars.yars import YARS

# Bright Data rotating residential proxy
proxy = "http://username-session-random123:password@brd.superproxy.io:22225"
miner = YARS(proxy=proxy, timeout=15)
```

Sign up: https://brightdata.com

#### B. Smartproxy (Recommended for Medium Usage)
Good balance of price/quality (~$75/month for 5GB)

```python
from yars.yars import YARS

# Smartproxy rotating residential proxy
proxy = "http://user:pass@gate.smartproxy.com:7000"
miner = YARS(proxy=proxy, timeout=15)
```

Sign up: https://smartproxy.com

#### C. Webshare (Budget-Friendly)
Cheap datacenter proxies (~$2.99/month for 10 proxies)

```python
from yars.yars import YARS

# Webshare proxy (rotate manually by changing proxy)
proxy = "http://username:password@proxy.webshare.io:80"
miner = YARS(proxy=proxy, timeout=15)
```

Sign up: https://www.webshare.io

#### D. ScraperAPI (Easiest, API-based)
Simple API-based solution (~$49/month for 100K requests)

```python
import requests
from yars.yars import YARS

# ScraperAPI proxy
api_key = "YOUR_SCRAPERAPI_KEY"
proxy = f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"
miner = YARS(proxy=proxy, timeout=20)
```

Sign up: https://www.scraperapi.com

### Option 3: DIY Proxy Rotation with Multiple Proxies

If you have a list of proxies, rotate them:

```python
from yars.yars import YARS
import random

# Your proxy list
PROXIES = [
    "http://user:pass@proxy1.example.com:8000",
    "http://user:pass@proxy2.example.com:8000",
    "http://user:pass@proxy3.example.com:8000",
]

def get_miner_with_random_proxy():
    proxy = random.choice(PROXIES)
    return YARS(proxy=proxy, timeout=15)

# Use it
miner = get_miner_with_random_proxy()
results = miner.search_reddit("AAPL stock", limit=10)

# Get a new miner with different proxy for next request
miner2 = get_miner_with_random_proxy()
results2 = miner2.search_reddit("NVDA stock", limit=10)
```

### Option 4: AWS-Based Proxy Solution (Self-Hosted)

If you want to handle proxies yourself on AWS:

1. **Launch EC2 Instances in Multiple Regions**
```bash
# Install Squid proxy on Ubuntu EC2
sudo apt update
sudo apt install squid -y
sudo nano /etc/squid/squid.conf
```

Add to squid.conf:
```
http_port 3128
http_access allow all
```

Restart:
```bash
sudo systemctl restart squid
```

2. **Use Your EC2 Proxies**
```python
from yars.yars import YARS

# Your EC2 proxy
proxy = "http://ec2-xx-xx-xx-xx.compute-1.amazonaws.com:3128"
miner = YARS(proxy=proxy, timeout=15)
```

**Note:** This requires managing multiple EC2 instances and rotating between them. Cost: ~$3.50/month per t2.micro instance.

### Recommended Setup for Stock Agent

For a production AI stock agent, I recommend:

```python
import os
from yars.yars import YARS
import time
import random

class StockRedditScraper:
    def __init__(self):
        # Load proxy from environment variable
        proxy = os.getenv('REDDIT_PROXY')

        if not proxy:
            print("WARNING: No proxy set! Use export REDDIT_PROXY='http://user:pass@proxy:port'")
            print("Running without proxy - expect IP bans for heavy scraping!")

        self.miner = YARS(proxy=proxy, timeout=15, random_user_agent=True)

    def scrape_with_rate_limit(self, subreddit, limit=50):
        """Scrape with built-in rate limiting"""
        posts = self.miner.fetch_subreddit_posts(
            subreddit,
            limit=limit,
            category="hot",
            time_filter="day"
        )

        # Add extra delay to be respectful
        time.sleep(random.uniform(2, 5))

        return posts

    def get_stock_sentiment_data(self, ticker):
        """Get sentiment data for a specific stock ticker"""
        # Search across multiple subreddits
        subreddits = ["wallstreetbets", "stocks", "investing", "stockmarket"]
        all_posts = []

        for sub in subreddits:
            try:
                # Search within subreddit
                results = self.miner.search_subreddit(
                    sub,
                    ticker,
                    limit=10
                )
                all_posts.extend(results)
                time.sleep(random.uniform(2, 4))  # Rate limiting
            except Exception as e:
                print(f"Error scraping {sub}: {e}")
                continue

        return all_posts

# Usage
if __name__ == "__main__":
    scraper = StockRedditScraper()

    # Get sentiment for TSLA
    tsla_posts = scraper.get_stock_sentiment_data("TSLA")
    print(f"Found {len(tsla_posts)} posts about TSLA")
```

Set your proxy:
```bash
export REDDIT_PROXY='http://username:password@proxy.example.com:8000'
python stock_scraper.py
```

---

## Integration with AI Stock Agent

### Architecture Recommendation

```
Your AI Stock Agent Repo
├── data_sources/
│   ├── reddit_scraper.py  # YARS integration
│   ├── news_scraper.py
│   └── market_data.py
├── sentiment_analysis/
│   ├── reddit_sentiment.py  # Analyze Reddit data
│   └── models/
├── trading_logic/
└── main.py
```

### Sample Integration

Create `data_sources/reddit_scraper.py` in your AI agent repo:

```python
import sys
import os

# Point to your YARS installation
YARS_PATH = os.path.expanduser("~/Projects/yars-stockagent/src")
sys.path.insert(0, YARS_PATH)

from yars.yars import YARS
import json
from datetime import datetime

class RedditDataSource:
    def __init__(self, proxy=None):
        self.miner = YARS(proxy=proxy, timeout=15)

    def get_daily_stock_discussions(self, tickers, subreddits=None):
        """
        Fetch daily stock discussions for sentiment analysis

        Args:
            tickers: List of stock tickers ["TSLA", "AAPL", "NVDA"]
            subreddits: List of subreddits to monitor

        Returns:
            Dictionary with structured data for your AI agent
        """
        if subreddits is None:
            subreddits = ["wallstreetbets", "stocks", "investing"]

        data = {
            "timestamp": datetime.now().isoformat(),
            "tickers": {}
        }

        for ticker in tickers:
            data["tickers"][ticker] = {
                "posts": [],
                "total_mentions": 0,
                "hot_discussions": []
            }

            # Get hot posts from each subreddit
            for sub in subreddits:
                try:
                    posts = self.miner.fetch_subreddit_posts(
                        sub,
                        limit=50,
                        category="hot",
                        time_filter="day"
                    )

                    # Filter posts mentioning the ticker
                    relevant_posts = [
                        p for p in posts
                        if ticker.upper() in p['title'].upper()
                    ]

                    data["tickers"][ticker]["posts"].extend(relevant_posts)
                    data["tickers"][ticker]["total_mentions"] += len(relevant_posts)

                except Exception as e:
                    print(f"Error scraping {sub} for {ticker}: {e}")
                    continue

        return data

    def get_detailed_post_for_sentiment(self, permalink):
        """Get full post with comments for deep sentiment analysis"""
        return self.miner.scrape_post_details(permalink)

# Usage in your AI agent
if __name__ == "__main__":
    proxy = os.getenv('REDDIT_PROXY')
    reddit = RedditDataSource(proxy=proxy)

    # Get data for your watchlist
    watchlist = ["TSLA", "AAPL", "NVDA", "GME", "AMC"]
    daily_data = reddit.get_daily_stock_discussions(watchlist)

    # Save for your sentiment analysis model
    with open('data/reddit_daily.json', 'w') as f:
        json.dump(daily_data, f, indent=2)

    print(f"Scraped data for {len(watchlist)} tickers")
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'yars'"

**Solution:** Make sure you're running with `uv run` or add the src path:
```python
import sys
sys.path.append('/path/to/yars-stockagent/src')
```

### Issue: "HTTP 429 Too Many Requests"

**Solution:** You're being rate limited. Use proxies and add delays:
```python
import time
import random

# Between requests
time.sleep(random.uniform(3, 7))
```

### Issue: "HTTP 403 Forbidden"

**Solution:** Your IP is banned. You must use rotating proxies. See [Rotating Proxies Setup](#rotating-proxies-setup).

### Issue: Proxy Connection Errors

**Solution:**
1. Test your proxy manually:
```bash
curl -x http://user:pass@proxy:port https://www.reddit.com
```

2. Increase timeout:
```python
miner = YARS(proxy=proxy, timeout=30)
```

### Issue: "SSL Certificate Verify Failed"

**Solution:** Some proxies have SSL issues:
```python
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
```

### Issue: Empty Results

**Solution:**
1. Check if subreddit exists
2. Try different time filters: "hour", "day", "week", "month", "year", "all"
3. Check Reddit status: https://www.redditstatus.com

---

## Best Practices for Stock Market Agent

1. **Rate Limiting:** Always add 2-5 second delays between requests
2. **Proxies:** Use rotating proxies for production (Smartproxy or Bright Data)
3. **Data Storage:** Save scraped data to avoid re-scraping
4. **Monitoring:** Track scraping success/failure rates
5. **Compliance:** Respect Reddit's Terms of Service
6. **Backup Sources:** Don't rely solely on Reddit - diversify data sources

### Recommended Subreddits for Stock Sentiment

```python
STOCK_SUBREDDITS = [
    "wallstreetbets",      # High volume, meme stocks
    "stocks",              # General stock discussion
    "investing",           # Long-term investment discussion
    "stockmarket",         # Market news and analysis
    "options",             # Options trading
    "pennystocks",         # Penny stocks
    "dividends",           # Dividend investing
    "algotrading",         # Algorithmic trading
    "SecurityAnalysis",    # Deep value analysis
    "ValueInvesting",      # Value investing
]
```

### Sample Cron Job for Daily Scraping

Add to your crontab (`crontab -e`):

```bash
# Run daily at 9 AM EST (before market open)
0 9 * * * cd ~/Projects/ai-stock-agent && /usr/local/bin/uv run scripts/daily_reddit_scrape.py

# Run every 4 hours during trading hours
0 9,13,17 * * 1-5 cd ~/Projects/ai-stock-agent && /usr/local/bin/uv run scripts/hourly_reddit_scrape.py
```

---

## Environment Variables Setup

Create a `.env` file in your AI agent repo:

```bash
# Reddit Scraping
REDDIT_PROXY=http://username:password@proxy.example.com:8000

# Optional: Multiple proxies (comma-separated)
REDDIT_PROXIES=http://proxy1:8000,http://proxy2:8000,http://proxy3:8000

# Rate limiting
REDDIT_DELAY_MIN=2
REDDIT_DELAY_MAX=5

# Logging
LOG_LEVEL=INFO
```

Load in your code:
```python
from dotenv import load_dotenv
load_dotenv()

proxy = os.getenv('REDDIT_PROXY')
```

Install python-dotenv:
```bash
uv pip install python-dotenv
```

---

## Next Steps

1. **Set up proxy service** - Start with Webshare for testing ($2.99/month)
2. **Test scraping** - Run example script with proxy
3. **Integrate with your AI agent** - Use the sample code above
4. **Set up monitoring** - Log scraping results and errors
5. **Scale up** - Add more proxies and subreddits as needed

---

## Support and Resources

- **YARS GitHub:** https://github.com/datavorous/yars
- **Reddit API Status:** https://www.redditstatus.com
- **Proxy Comparison:** https://www.trustpilot.com (search for proxy services)

## Quick Command Reference

```bash
# Install YARS
git clone https://github.com/datavorous/YARS.git yars-stockagent
cd yars-stockagent
pip3 install uv

# Run example
uv run example/example.py

# Run your script
uv run your_script.py

# Set proxy
export REDDIT_PROXY='http://user:pass@proxy:port'

# Test proxy
curl -x $REDDIT_PROXY https://www.reddit.com
```

---

**Ready to scrape!** Start with the example script, add a proxy, and integrate with your AI stock agent. Good luck with your trading bot!
