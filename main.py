#!/usr/bin/env python3
"""
TrendBot - Social Media Trend Analysis Bot
A personal project to monitor and analyze trending topics across social platforms
"""

import asyncio
from datetime import datetime

from src.config import Config
from src.logger import setup_logging, get_logger
from src.twitter_client import TwitterClient
from src.reddit_client import RedditClient
from src.database import TrendDatabase, TrendRecord

# Setup logging
setup_logging()
logger = get_logger(__name__)


class TrendBot:
    def __init__(self):
        self.name = "TrendBot"
        self.version = "0.2.0"
        self.config = Config.from_env()
        self.twitter_client = TwitterClient(self.config.twitter)
        self.reddit_client = RedditClient(self.config.reddit)
        self.database = TrendDatabase(self.config.database.db_path)
        logger.info(f"Initializing {self.name} v{self.version}")

    async def start(self):
        """Start the trend monitoring bot"""
        logger.info("Starting trend analysis...")
        print(f"🤖 {self.name} v{self.version} is starting up...")
        print("🔍 Ready to monitor social media trends")

        # Test Twitter integration
        print("\n📱 Testing Twitter API...")
        twitter_trends = await self.twitter_client.get_trending_topics()
        if twitter_trends:
            print(f"✅ Found {len(twitter_trends)} Twitter trends")
            for trend in twitter_trends[:2]:
                print(f"  - {trend['name']}")
        else:
            print("⚠️  No Twitter trends found")

        # Test Reddit integration
        print("\n🔴 Testing Reddit API...")
        reddit_topics = await self.reddit_client.get_hot_topics(['technology', 'worldnews'], limit=5)
        if reddit_topics:
            print(f"✅ Found {len(reddit_topics)} Reddit hot topics")
            for topic in reddit_topics[:2]:
                print(f"  - r/{topic['subreddit']}: {topic['title'][:50]}...")
        else:
            print("⚠️  No Reddit topics found")

        # Show recent trends from database
        print("\n💾 Recent trends from database:")
        recent = self.database.get_recent_trends(limit=5)
        if recent:
            for trend in recent:
                print(f"  - [{trend['platform']}] {trend['topic']} (score: {trend['score']})")
        else:
            print("  No recent trends in database")


async def main():
    """Main entry point"""
    bot = TrendBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())