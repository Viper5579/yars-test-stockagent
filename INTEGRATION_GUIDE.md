# Quick Integration Guide for Your Stock Agent

## TL;DR - 5 Minute Setup

### 1. Install YARS (this repo)

```bash
cd ~/Projects
git clone https://github.com/datavorous/YARS.git yars-stockagent
cd yars-stockagent
pip3 install uv
uv run example/stock_agent_drop_in.py  # Test it works
```

### 2. Get a Proxy

**Cheapest option:**
- Sign up: https://www.webshare.io
- Get 10 proxies for $2.99/month
- Copy your proxy credentials

### 3. Update Your Stock Agent Config

In your `stock-agent-test` config file, update the social_sentiment section:

```json
{
  "social_sentiment": {
    "enabled": true,
    "reddit_enabled": true,
    "reddit_proxy": "http://username:password@proxy.webshare.io:80",
    "subreddits": ["wallstreetbets", "stocks", "investing"],
    "rate_limit_per_minute": 30
  }
}
```

Just add the `reddit_proxy` line with your proxy URL.

**You NO LONGER need these** (YARS doesn't use official API):
- ~~reddit_client_id~~
- ~~reddit_client_secret~~
- ~~reddit_user_agent~~

### 4. Copy the Module to Your Stock Agent

```bash
# In your stock-agent-test repo
cp ~/Projects/yars-stockagent/example/stock_agent_drop_in.py ./reddit_sentiment.py
```

### 5. Use It in Your Agent

Replace your existing Reddit API code with:

```python
from reddit_sentiment import RedditSentimentClient
import json

# Load your config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize Reddit client (no API keys needed!)
reddit = RedditSentimentClient(config['social_sentiment'])

# Get hot posts from configured subreddits
posts = reddit.get_multi_subreddit_posts(limit_per_sub=50)

# Search for specific tickers
watchlist = ["TSLA", "NVDA", "AAPL"]
sentiment_data = reddit.get_sentiment_data(watchlist, limit_per_ticker=20)

# Use the data
for ticker, data in sentiment_data.items():
    mentions = data['total_mentions']
    if mentions > 50:
        print(f"🔥 {ticker} is trending! {mentions} mentions")
```

### 6. Test It

```bash
cd ~/Projects/stock-agent-test
export REDDIT_PROXY='http://username:password@proxy.webshare.io:80'
python3 test_reddit.py  # or however you run your agent
```

---

## API Reference

### Initialize Client

```python
reddit = RedditSentimentClient(config['social_sentiment'])
```

### Get Posts from Subreddit

```python
posts = reddit.get_subreddit_posts(
    'wallstreetbets',
    limit=50,
    category='hot',      # 'hot', 'top', or 'new'
    time_filter='day'    # 'hour', 'day', 'week', 'month', 'year', 'all'
)

# Returns list of dicts:
# [
#   {
#     'title': '...',
#     'author': '...',
#     'score': 1234,
#     'num_comments': 567,
#     'permalink': '/r/wallstreetbets/comments/...',
#     'created_utc': 1234567890
#   },
#   ...
# ]
```

### Search for Ticker

```python
posts = reddit.search_ticker(
    'TSLA',
    subreddits=['wallstreetbets', 'stocks'],  # Optional, uses config default
    limit_per_subreddit=20
)

# Returns posts mentioning 'TSLA'
```

### Get Sentiment for Multiple Tickers

```python
sentiment_data = reddit.get_sentiment_data(
    tickers=['TSLA', 'NVDA', 'AAPL'],
    limit_per_ticker=20
)

# Returns:
# {
#   'TSLA': {
#     'ticker': 'TSLA',
#     'timestamp': '2025-11-20T...',
#     'total_mentions': 45,
#     'posts': [...],
#     'by_subreddit': {'wallstreetbets': 30, 'stocks': 15}
#   },
#   ...
# }
```

### Get Post Details (with all comments)

```python
details = reddit.get_post_details('/r/wallstreetbets/comments/abc123/...')

# Returns:
# {
#   'title': '...',
#   'body': '...',
#   'comments': [
#     {
#       'author': '...',
#       'body': '...',
#       'score': 123,
#       'replies': [...]
#     },
#     ...
#   ]
# }
```

---

## Config Options

```json
{
  "social_sentiment": {
    "enabled": true,                  // Enable/disable Reddit scraping
    "reddit_enabled": true,           // Reddit-specific toggle
    "reddit_proxy": "http://...",     // REQUIRED: Proxy URL
    "subreddits": [                   // Subreddits to monitor
      "wallstreetbets",
      "stocks",
      "investing",
      "stockmarket"
    ],
    "rate_limit_per_minute": 30       // Max requests per minute
  }
}
```

Or use environment variable:
```bash
export REDDIT_PROXY='http://user:pass@proxy:port'
```

---

## Production Setup

### Option 1: Environment Variables (Recommended)

```bash
# Add to ~/.zshrc or ~/.bash_profile
export REDDIT_PROXY='http://user:pass@proxy:port'
```

### Option 2: Config File

Store proxy in your config.json (don't commit to git!)

```json
{
  "social_sentiment": {
    "reddit_proxy": "http://user:pass@proxy.webshare.io:80"
  }
}
```

Add to .gitignore:
```
config.json
.env
```

### Option 3: Multiple Proxies (Advanced)

For higher volume, rotate between multiple proxies:

```python
import random

class MultiProxyRedditClient:
    def __init__(self, config):
        self.proxies = config.get('reddit_proxies', [])
        self.config = config

    def get_client(self):
        # Get random proxy
        proxy = random.choice(self.proxies)
        config = {**self.config, 'reddit_proxy': proxy}
        return RedditSentimentClient(config)

# Usage
proxies = [
    "http://user:pass@proxy1:80",
    "http://user:pass@proxy2:80",
    "http://user:pass@proxy3:80"
]

config = {
    'reddit_proxies': proxies,
    'subreddits': ['wallstreetbets', 'stocks'],
    'rate_limit_per_minute': 30
}

multi_client = MultiProxyRedditClient(config)
reddit = multi_client.get_client()  # Gets new proxy each time
```

---

## Proxy Recommendations

### For Testing
**Webshare** - $2.99/month for 10 proxies
- Sign up: https://www.webshare.io
- Good for testing, limited volume

### For Production
**Smartproxy** - $75/month for 5GB
- Sign up: https://smartproxy.com
- Residential IPs, harder to detect

**Bright Data** - $500+/month
- Sign up: https://brightdata.com
- Enterprise-grade, most reliable

---

## Example: Daily Sentiment Collection

Create a script for your cron job:

```python
#!/usr/bin/env python3
"""
Collect daily Reddit sentiment
Run via cron: 0 9 * * * python3 collect_sentiment.py
"""

import json
from reddit_sentiment import RedditSentimentClient
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize
reddit = RedditSentimentClient(config['social_sentiment'])

# Get sentiment
watchlist = config.get('stock_watchlist', ['TSLA', 'NVDA', 'AAPL'])
sentiment = reddit.get_sentiment_data(watchlist, limit_per_ticker=30)

# Save results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'data/reddit_sentiment_{timestamp}.json'

with open(filename, 'w') as f:
    json.dump(sentiment, f, indent=2)

print(f"✓ Saved to {filename}")

# Log summary
for ticker, data in sentiment.items():
    print(f"{ticker}: {data['total_mentions']} mentions")
```

Add to crontab:
```bash
crontab -e

# Run daily at 9 AM
0 9 * * * cd ~/Projects/stock-agent-test && python3 collect_sentiment.py
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'yars'"

The module tries to find YARS automatically in these locations:
1. `../src` (if YARS is in parent directory)
2. `~/Projects/yars-stockagent/src`

If your YARS is elsewhere, add to top of your script:
```python
import sys
sys.path.insert(0, '/path/to/yars-stockagent/src')
```

### "WARNING: No proxy configured"

Set the proxy:
```bash
export REDDIT_PROXY='http://user:pass@proxy:port'
```

Or add to config:
```json
{
  "social_sentiment": {
    "reddit_proxy": "http://user:pass@proxy:port"
  }
}
```

### Rate Limiting / 429 Errors

Reduce rate limit in config:
```json
{
  "rate_limit_per_minute": 15  // Slower but safer
}
```

### Proxy Connection Errors

Test your proxy:
```bash
curl -x http://user:pass@proxy:port https://www.reddit.com
```

If it fails, your proxy credentials are wrong or proxy is down.

---

## Complete Example

Here's a complete working example:

```python
#!/usr/bin/env python3
"""Complete stock agent Reddit integration example"""

import json
from reddit_sentiment import RedditSentimentClient

# Your config
config = {
    "social_sentiment": {
        "enabled": True,
        "reddit_enabled": True,
        "reddit_proxy": "http://user:pass@proxy.webshare.io:80",
        "subreddits": ["wallstreetbets", "stocks", "investing"],
        "rate_limit_per_minute": 30
    }
}

# Initialize client
reddit = RedditSentimentClient(config['social_sentiment'])

# Your trading watchlist
watchlist = ["TSLA", "NVDA", "AAPL", "AMD", "MSFT"]

# Get sentiment data
print("Collecting Reddit sentiment...")
sentiment_data = reddit.get_sentiment_data(watchlist, limit_per_ticker=20)

# Analyze and make decisions
for ticker, data in sentiment_data.items():
    mentions = data['total_mentions']
    by_sub = data['by_subreddit']

    print(f"\n{ticker}:")
    print(f"  Total mentions: {mentions}")
    print(f"  Distribution: {by_sub}")

    # Your trading logic here
    if mentions > 50:
        print(f"  🔥 HIGH ACTIVITY - Consider this in trading decision")

    # Example: Check if trending on WSB
    wsb_mentions = by_sub.get('wallstreetbets', 0)
    if wsb_mentions > 20:
        print(f"  🚀 TRENDING ON WSB - Potential volatility")

    # Get detailed analysis of top posts
    if data['posts']:
        top_post = data['posts'][0]
        details = reddit.get_post_details(top_post['link'].split('reddit.com')[1])

        if details:
            print(f"  Top post: {details['title']}")
            print(f"  Comments: {len(details['comments'])}")

# Save results
with open('sentiment_results.json', 'w') as f:
    json.dump(sentiment_data, f, indent=2)

print("\n✓ Done! Results saved to sentiment_results.json")
```

---

## Next Steps

1. ✅ Set up proxy (Webshare for $2.99/month)
2. ✅ Copy `stock_agent_drop_in.py` to your agent repo
3. ✅ Update your config with `reddit_proxy`
4. ✅ Test the integration
5. ✅ Integrate into your trading logic
6. ✅ Set up automated collection (cron)

---

**Questions? See:**
- [Mac Quickstart Guide](MAC_QUICKSTART.md) - Detailed setup
- [Full Integration Guide](STOCK_AGENT_INTEGRATION.md) - Advanced usage
- [Example Scripts](example/) - Working code examples

**Ready to scrape! 📈**
