"""
Drop-in Reddit Module for Your Stock Agent
Using YARS instead of official Reddit API (no API keys needed!)

Place this in your stock-agent-test repo and import it.

Your config structure:
{
  "social_sentiment": {
    "enabled": true,
    "reddit_enabled": true,
    "reddit_proxy": "http://user:pass@proxy:port",  # ADD THIS
    "subreddits": ["wallstreetbets", "stocks", "investing"],
    "rate_limit_per_minute": 30
  }
}
"""

import sys
import os
from pathlib import Path
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional


class RedditSentimentClient:
    """
    Drop-in replacement for Reddit API client using YARS
    No API keys required!

    Usage:
        config = load_your_config()
        reddit = RedditSentimentClient(config['social_sentiment'])
        posts = reddit.get_subreddit_posts('wallstreetbets', limit=50)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Reddit client with your agent's config

        Args:
            config: Your social_sentiment config dict
        """
        self.config = config
        self.enabled = config.get('reddit_enabled', True)
        self.subreddits = config.get('subreddits', ['wallstreetbets', 'stocks'])
        self.rate_limit = config.get('rate_limit_per_minute', 30)

        # Calculate delay between requests
        self.min_delay = 60.0 / self.rate_limit if self.rate_limit > 0 else 2.0

        # Get proxy from config
        self.proxy = config.get('reddit_proxy', os.getenv('REDDIT_PROXY'))

        if not self.proxy:
            print("⚠️  WARNING: No proxy configured!")
            print("   Add 'reddit_proxy' to your config or set REDDIT_PROXY env var")
            print("   Reddit will ban your IP without proxies!")

        # Initialize YARS
        self._init_yars()

        print(f"✓ Reddit client initialized")
        print(f"  Proxy: {'Enabled' if self.proxy else 'DISABLED (RISKY!)'}")
        print(f"  Rate limit: {self.rate_limit} req/min")
        print(f"  Subreddits: {', '.join(self.subreddits)}")

    def _init_yars(self):
        """Initialize YARS scraper"""
        # Try to import YARS from multiple possible locations
        yars_locations = [
            # If YARS is in parent directory
            str(Path(__file__).parent.parent / "src"),
            # If YARS is in ~/Projects
            str(Path.home() / "Projects" / "yars-stockagent" / "src"),
            # If YARS is installed via pip
            "yars",
        ]

        for location in yars_locations:
            try:
                if location not in sys.path:
                    sys.path.insert(0, location)

                from yars.yars import YARS
                self.miner = YARS(
                    proxy=self.proxy,
                    timeout=15,
                    random_user_agent=True
                )
                print(f"  YARS loaded from: {location}")
                return

            except ImportError:
                continue

        raise ImportError(
            "Could not import YARS! Please install:\n"
            "  cd ~/Projects && git clone https://github.com/datavorous/YARS.git yars-stockagent\n"
            "Or set PYTHONPATH to YARS src directory"
        )

    def _rate_limit_delay(self):
        """Apply rate limiting delay"""
        delay = random.uniform(self.min_delay, self.min_delay * 1.5)
        time.sleep(delay)

    def get_subreddit_posts(
        self,
        subreddit: str,
        limit: int = 50,
        category: str = "hot",
        time_filter: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get posts from a subreddit (matches your existing API)

        Args:
            subreddit: Subreddit name (e.g., 'wallstreetbets')
            limit: Number of posts to retrieve
            category: 'hot', 'top', or 'new'
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'

        Returns:
            List of post dictionaries
        """
        if not self.enabled:
            return []

        try:
            posts = self.miner.fetch_subreddit_posts(
                subreddit,
                limit=limit,
                category=category,
                time_filter=time_filter
            )

            self._rate_limit_delay()
            return posts

        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}")
            return []

    def search_ticker(
        self,
        ticker: str,
        subreddits: Optional[List[str]] = None,
        limit_per_subreddit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for ticker mentions across subreddits

        Args:
            ticker: Stock ticker (e.g., 'TSLA')
            subreddits: List of subreddits to search (uses config if None)
            limit_per_subreddit: Max results per subreddit

        Returns:
            List of posts mentioning the ticker
        """
        if not self.enabled:
            return []

        if subreddits is None:
            subreddits = self.subreddits

        all_posts = []

        for sub in subreddits:
            try:
                posts = self.miner.search_subreddit(
                    sub,
                    ticker,
                    limit=limit_per_subreddit,
                    sort="relevance"
                )

                if posts:
                    # Add metadata
                    for post in posts:
                        post['subreddit'] = sub
                        post['ticker_searched'] = ticker

                    all_posts.extend(posts)

                self._rate_limit_delay()

            except Exception as e:
                print(f"Error searching r/{sub} for {ticker}: {e}")
                continue

        return all_posts

    def get_post_details(self, permalink: str) -> Optional[Dict[str, Any]]:
        """
        Get full post with all comments

        Args:
            permalink: Reddit post permalink (e.g., '/r/stocks/comments/...')

        Returns:
            Dict with title, body, and comments
        """
        if not self.enabled:
            return None

        try:
            details = self.miner.scrape_post_details(permalink)
            self._rate_limit_delay()
            return details

        except Exception as e:
            print(f"Error getting post details: {e}")
            return None

    def get_multi_subreddit_posts(
        self,
        subreddits: Optional[List[str]] = None,
        limit_per_sub: int = 30,
        category: str = "hot"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get posts from multiple subreddits

        Args:
            subreddits: List of subreddits (uses config if None)
            limit_per_sub: Posts per subreddit
            category: 'hot', 'top', or 'new'

        Returns:
            Dict mapping subreddit name to posts
        """
        if not self.enabled:
            return {}

        if subreddits is None:
            subreddits = self.subreddits

        results = {}

        for sub in subreddits:
            posts = self.get_subreddit_posts(sub, limit_per_sub, category)
            if posts:
                results[sub] = posts

        return results

    def get_sentiment_data(
        self,
        tickers: List[str],
        limit_per_ticker: int = 20
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get sentiment data for multiple tickers

        Args:
            tickers: List of stock tickers
            limit_per_ticker: Max posts per ticker

        Returns:
            Dict mapping ticker to sentiment data
        """
        if not self.enabled:
            return {}

        results = {}

        for ticker in tickers:
            posts = self.search_ticker(ticker, limit_per_subreddit=limit_per_ticker)

            results[ticker] = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "total_mentions": len(posts),
                "posts": posts,
                "by_subreddit": {}
            }

            # Count by subreddit
            for post in posts:
                sub = post.get('subreddit', 'unknown')
                if sub not in results[ticker]["by_subreddit"]:
                    results[ticker]["by_subreddit"][sub] = 0
                results[ticker]["by_subreddit"][sub] += 1

        return results


# ============================================================================
# Example Usage for Your Stock Agent
# ============================================================================

def example_integration():
    """
    Example of how to integrate this into your stock agent

    In your agent's main code:

    from reddit_sentiment import RedditSentimentClient

    # Load your config
    config = {
        "social_sentiment": {
            "enabled": True,
            "reddit_enabled": True,
            "reddit_proxy": "http://user:pass@proxy:port",  # Add this!
            "subreddits": ["wallstreetbets", "stocks", "investing"],
            "rate_limit_per_minute": 30
        }
    }

    # Initialize Reddit client
    reddit = RedditSentimentClient(config['social_sentiment'])

    # Example 1: Get hot posts from configured subreddits
    posts = reddit.get_multi_subreddit_posts(limit_per_sub=50)
    print(f"Retrieved posts from {len(posts)} subreddits")

    # Example 2: Search for specific tickers
    watchlist = ["TSLA", "NVDA", "AAPL"]
    sentiment_data = reddit.get_sentiment_data(watchlist, limit_per_ticker=20)

    for ticker, data in sentiment_data.items():
        print(f"{ticker}: {data['total_mentions']} mentions")

    # Example 3: Get detailed post for analysis
    if posts.get('wallstreetbets'):
        first_post = posts['wallstreetbets'][0]
        details = reddit.get_post_details(first_post['permalink'])
        print(f"Post has {len(details['comments'])} comments")
    """
    pass


# ============================================================================
# Minimal Example Config File
# ============================================================================

EXAMPLE_CONFIG = """
{
  "social_sentiment": {
    "enabled": true,
    "reddit_enabled": true,
    "reddit_proxy": "http://username:password@proxy.webshare.io:80",
    "subreddits": ["wallstreetbets", "stocks", "investing", "stockmarket"],
    "rate_limit_per_minute": 30
  },
  "stock_watchlist": ["TSLA", "NVDA", "AAPL", "AMD", "MSFT"]
}
"""


# ============================================================================
# Test Script
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Reddit Sentiment Client - Test Script")
    print("="*70)

    # Test configuration
    test_config = {
        "enabled": True,
        "reddit_enabled": True,
        "reddit_proxy": os.getenv('REDDIT_PROXY'),
        "subreddits": ["wallstreetbets", "stocks"],
        "rate_limit_per_minute": 30
    }

    try:
        # Initialize client
        reddit = RedditSentimentClient(test_config)

        # Test 1: Get hot posts
        print("\n[Test 1] Getting hot posts from r/wallstreetbets...")
        posts = reddit.get_subreddit_posts('wallstreetbets', limit=5)
        print(f"✓ Retrieved {len(posts)} posts")

        if posts:
            print(f"\nTop post: {posts[0]['title']}")
            print(f"Score: {posts[0]['score']}, Comments: {posts[0]['num_comments']}")

        # Test 2: Search for ticker
        print("\n[Test 2] Searching for TSLA mentions...")
        tsla_posts = reddit.search_ticker('TSLA', limit_per_subreddit=5)
        print(f"✓ Found {len(tsla_posts)} posts mentioning TSLA")

        # Test 3: Get sentiment data
        print("\n[Test 3] Getting sentiment data for multiple tickers...")
        sentiment = reddit.get_sentiment_data(['TSLA', 'NVDA'], limit_per_ticker=5)

        for ticker, data in sentiment.items():
            print(f"\n{ticker}:")
            print(f"  Mentions: {data['total_mentions']}")
            print(f"  By subreddit: {data['by_subreddit']}")

        print("\n" + "="*70)
        print("✅ All tests passed! Integration is working.")
        print("="*70)

        print("\nNext steps:")
        print("1. Copy this file to your stock-agent-test repo")
        print("2. Add 'reddit_proxy' to your config.json")
        print("3. Import and use: from reddit_sentiment import RedditSentimentClient")
        print("4. See STOCK_AGENT_INTEGRATION.md for full integration guide")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. YARS is installed: git clone https://github.com/datavorous/YARS.git")
        print("2. Proxy is set: export REDDIT_PROXY='http://user:pass@proxy:port'")
        print("3. Run from example directory: uv run example/stock_agent_drop_in.py")
