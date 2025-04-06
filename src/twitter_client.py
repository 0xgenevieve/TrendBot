"""
Twitter API client for fetching trending topics
"""

import logging
import tweepy
from typing import List, Dict, Optional
from src.config import TwitterConfig

logger = logging.getLogger(__name__)


class TwitterClient:
    def __init__(self, config: TwitterConfig):
        self.config = config
        self.client = None
        self._setup_client()

    def _setup_client(self):
        """Initialize Twitter API client"""
        if not self.config.bearer_token:
            logger.warning("No Twitter bearer token provided")
            return

        try:
            self.client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=True
            )
            logger.info("Twitter client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")

    async def get_trending_topics(self, woeid: int = 1) -> List[Dict]:
        """
        Get trending topics for a specific location
        woeid: Where On Earth ID (1 = worldwide)
        """
        if not self.client:
            logger.error("Twitter client not initialized")
            return []

        try:
            # Note: This is a placeholder - Twitter API v2 doesn't have direct trending endpoint
            # We'll need to implement search-based trending analysis
            logger.info(f"Fetching trending topics for WOEID: {woeid}")

            # TODO: Implement actual trending logic using search API
            # For now, return mock data
            return [
                {"name": "#trending1", "volume": 50000},
                {"name": "#trending2", "volume": 30000}
            ]
        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []

    async def search_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for tweets containing specific keywords"""
        if not self.client:
            logger.error("Twitter client not initialized")
            return []

        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            ).flatten(limit=max_results)

            results = []
            for tweet in tweets:
                results.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'author_id': tweet.author_id,
                    'metrics': tweet.public_metrics
                })

            logger.info(f"Found {len(results)} tweets for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []