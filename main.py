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

# Setup logging
setup_logging()
logger = get_logger(__name__)


class TrendBot:
    def __init__(self):
        self.name = "TrendBot"
        self.version = "0.1.0"
        self.config = Config.from_env()
        self.twitter_client = TwitterClient(self.config.twitter)
        logger.info(f"Initializing {self.name} v{self.version}")

    async def start(self):
        """Start the trend monitoring bot"""
        logger.info("Starting trend analysis...")
        print(f"🤖 {self.name} is starting up...")
        print("🔍 Ready to monitor social media trends")

        # Test Twitter integration
        trends = await self.twitter_client.get_trending_topics()
        if trends:
            print(f"📈 Found {len(trends)} trending topics")
            for trend in trends[:3]:
                print(f"  - {trend['name']}")
        else:
            print("⚠️  No trends found (check API configuration)")


async def main():
    """Main entry point"""
    bot = TrendBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())