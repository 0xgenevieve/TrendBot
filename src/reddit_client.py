"""
Reddit API client for fetching hot topics from various subreddits
"""

import logging
import praw
from typing import List, Dict, Optional
from src.config import RedditConfig

logger = logging.getLogger(__name__)


class RedditClient:
    def __init__(self, config: RedditConfig):
        self.config = config
        self.reddit = None
        self._setup_client()

    def _setup_client(self):
        """Initialize Reddit API client"""
        if not self.config.client_id or not self.config.client_secret:
            logger.warning("Reddit API credentials not provided")
            return

        try:
            self.reddit = praw.Reddit(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                user_agent=self.config.user_agent
            )
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")

    async def get_hot_topics(self, subreddit_names: List[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get hot topics from specified subreddits
        """
        if not self.reddit:
            logger.error("Reddit client not initialized")
            return []

        if not subreddit_names:
            subreddit_names = ['all', 'popular', 'worldnews', 'technology']

        hot_topics = []

        try:
            for sub_name in subreddit_names:
                logger.info(f"Fetching hot posts from r/{sub_name}")
                subreddit = self.reddit.subreddit(sub_name)

                for submission in subreddit.hot(limit=limit):
                    hot_topics.append({
                        'id': submission.id,
                        'title': submission.title,
                        'subreddit': submission.subreddit.display_name,
                        'score': submission.score,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'created_utc': submission.created_utc,
                        'url': submission.url,
                        'permalink': f"https://reddit.com{submission.permalink}"
                    })

            logger.info(f"Fetched {len(hot_topics)} hot topics from Reddit")
            return hot_topics

        except Exception as e:
            logger.error(f"Error fetching Reddit hot topics: {e}")
            return []

    async def search_posts(self, query: str, subreddit_name: str = 'all',
                          time_filter: str = 'day', limit: int = 10) -> List[Dict]:
        """Search for posts containing specific keywords"""
        if not self.reddit:
            logger.error("Reddit client not initialized")
            return []

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            results = []

            for submission in subreddit.search(query, time_filter=time_filter, limit=limit):
                results.append({
                    'id': submission.id,
                    'title': submission.title,
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'url': submission.url,
                    'selftext': submission.selftext[:200] if submission.selftext else ""
                })

            logger.info(f"Found {len(results)} posts for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching Reddit posts: {e}")
            return []

    def get_trending_subreddits(self, limit: int = 20) -> List[str]:
        """Get list of trending subreddit names"""
        if not self.reddit:
            logger.error("Reddit client not initialized")
            return []

        try:
            trending = []
            for subreddit in self.reddit.subreddits.popular(limit=limit):
                trending.append(subreddit.display_name)

            logger.info(f"Found {len(trending)} trending subreddits")
            return trending

        except Exception as e:
            logger.error(f"Error fetching trending subreddits: {e}")
            return []