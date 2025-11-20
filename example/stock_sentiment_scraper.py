"""
Stock Sentiment Scraper for AI Investment Agents
Uses YARS to scrape Reddit for stock market sentiment analysis

Usage:
    uv run example/stock_sentiment_scraper.py

    Or with proxy:
    export REDDIT_PROXY='http://user:pass@proxy:port'
    uv run example/stock_sentiment_scraper.py
"""

import json
import os
import sys
import time
import random
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)

from yars.yars import YARS
from yars.utils import display_results


class StockSentimentScraper:
    """Scraper specifically designed for stock market sentiment analysis"""

    def __init__(self, proxy=None, verbose=True):
        """
        Initialize the stock sentiment scraper

        Args:
            proxy: Proxy URL (format: http://user:pass@host:port)
            verbose: Print progress messages
        """
        self.proxy = proxy
        self.verbose = verbose

        if proxy:
            self.log(f"✓ Using proxy: {proxy[:30]}...")
        else:
            self.log("⚠ WARNING: No proxy configured! Reddit may ban your IP.")
            self.log("  Set REDDIT_PROXY environment variable or pass proxy parameter")

        self.miner = YARS(proxy=proxy, timeout=15, random_user_agent=True)

        # Stock-focused subreddits
        self.stock_subreddits = [
            "wallstreetbets",
            "stocks",
            "investing",
            "stockmarket",
            "options"
        ]

    def log(self, message):
        """Print message if verbose mode is on"""
        if self.verbose:
            print(message)

    def scrape_ticker_sentiment(self, ticker, max_posts=30):
        """
        Scrape Reddit for sentiment on a specific stock ticker

        Args:
            ticker: Stock ticker symbol (e.g., "TSLA", "AAPL")
            max_posts: Maximum posts to retrieve per subreddit

        Returns:
            Dictionary containing scraped posts and metadata
        """
        self.log(f"\n{'='*60}")
        self.log(f"Scraping sentiment for: {ticker}")
        self.log(f"{'='*60}")

        results = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "total_posts": 0,
            "by_subreddit": {},
            "all_posts": []
        }

        for subreddit in self.stock_subreddits:
            self.log(f"\nSearching r/{subreddit}...")

            try:
                # Search within subreddit for the ticker
                posts = self.miner.search_subreddit(
                    subreddit,
                    ticker,
                    limit=max_posts,
                    sort="relevance"
                )

                if posts:
                    results["by_subreddit"][subreddit] = len(posts)
                    results["total_posts"] += len(posts)
                    results["all_posts"].extend([
                        {
                            **post,
                            "subreddit": subreddit,
                            "ticker": ticker
                        }
                        for post in posts
                    ])
                    self.log(f"  ✓ Found {len(posts)} posts")
                else:
                    self.log(f"  - No posts found")

                # Rate limiting - be respectful to Reddit
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                self.log(f"  ✗ Error: {e}")
                continue

        return results

    def scrape_multiple_tickers(self, tickers, max_posts_per_ticker=20):
        """
        Scrape sentiment for multiple stock tickers

        Args:
            tickers: List of ticker symbols
            max_posts_per_ticker: Max posts per ticker per subreddit

        Returns:
            Dictionary with results for all tickers
        """
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "tickers": {}
        }

        for ticker in tickers:
            ticker_data = self.scrape_ticker_sentiment(ticker, max_posts_per_ticker)
            all_results["tickers"][ticker] = ticker_data

            # Extra delay between tickers
            time.sleep(random.uniform(3, 6))

        return all_results

    def scrape_hot_stocks(self, subreddit="wallstreetbets", limit=50):
        """
        Get hot/trending posts from a stock subreddit

        Args:
            subreddit: Subreddit name
            limit: Number of posts to retrieve

        Returns:
            List of post data
        """
        self.log(f"\nFetching hot posts from r/{subreddit}...")

        try:
            posts = self.miner.fetch_subreddit_posts(
                subreddit,
                limit=limit,
                category="hot",
                time_filter="day"
            )
            self.log(f"✓ Retrieved {len(posts)} hot posts")
            return posts
        except Exception as e:
            self.log(f"✗ Error: {e}")
            return []

    def get_post_details_with_comments(self, permalink):
        """
        Get full post content including all comments for deep sentiment analysis

        Args:
            permalink: Reddit post permalink

        Returns:
            Dictionary with post title, body, and all comments
        """
        self.log(f"\nFetching detailed post data...")

        try:
            details = self.miner.scrape_post_details(permalink)
            if details:
                num_comments = len(details.get('comments', []))
                self.log(f"✓ Retrieved post with {num_comments} comments")
            return details
        except Exception as e:
            self.log(f"✗ Error: {e}")
            return None

    def save_results(self, data, filename):
        """Save results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.log(f"\n✓ Results saved to: {filename}")
        except Exception as e:
            self.log(f"\n✗ Error saving results: {e}")


def main():
    """Example usage of the Stock Sentiment Scraper"""

    # Get proxy from environment variable
    proxy = os.getenv('REDDIT_PROXY')

    # Initialize scraper
    scraper = StockSentimentScraper(proxy=proxy)

    print("\n" + "="*60)
    print("YARS Stock Sentiment Scraper - Example Usage")
    print("="*60)

    # Example 1: Scrape sentiment for specific tickers
    print("\n[1] Scraping specific tickers...")
    watchlist = ["TSLA", "NVDA", "AAPL"]
    ticker_results = scraper.scrape_multiple_tickers(watchlist, max_posts_per_ticker=10)

    # Display summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    for ticker, data in ticker_results["tickers"].items():
        print(f"\n{ticker}:")
        print(f"  Total posts found: {data['total_posts']}")
        print(f"  By subreddit:")
        for sub, count in data['by_subreddit'].items():
            print(f"    - r/{sub}: {count} posts")

    # Save results
    scraper.save_results(ticker_results, "stock_sentiment_data.json")

    # Example 2: Get hot posts from WallStreetBets
    print("\n" + "="*60)
    print("[2] Getting hot posts from r/wallstreetbets...")
    print("="*60)
    hot_posts = scraper.scrape_hot_stocks("wallstreetbets", limit=10)

    if hot_posts:
        print(f"\nTop 5 hot posts:")
        for i, post in enumerate(hot_posts[:5], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
            print(f"   https://reddit.com{post['permalink']}")

    # Example 3: Get detailed post with comments for sentiment analysis
    if hot_posts:
        print("\n" + "="*60)
        print("[3] Getting detailed post with comments...")
        print("="*60)
        first_post = hot_posts[0]
        post_details = scraper.get_post_details_with_comments(first_post['permalink'])

        if post_details:
            print(f"\nPost: {post_details['title']}")
            print(f"Comments retrieved: {len(post_details['comments'])}")
            print("\nFirst 3 comments:")
            for i, comment in enumerate(post_details['comments'][:3], 1):
                comment_text = comment['body'][:100] + "..." if len(comment['body']) > 100 else comment['body']
                print(f"{i}. [{comment['author']}]: {comment_text}")
                print(f"   Score: {comment['score']}")

    print("\n" + "="*60)
    print("Done! Check stock_sentiment_data.json for full results")
    print("="*60)

    # Tips for integration
    print("\n💡 Integration Tips:")
    print("1. Use this data as input for your sentiment analysis model")
    print("2. Track score, num_comments, and comment sentiment over time")
    print("3. Set up cron jobs to run this daily/hourly")
    print("4. Combine with other data sources (news, market data, etc.)")
    print("5. Always use rotating proxies in production!")
    print("\nFor proxy setup, see: MAC_QUICKSTART.md")


if __name__ == "__main__":
    main()
