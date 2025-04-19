#!/usr/bin/env python3
"""
TrendBot - Social Media Trend Analysis Bot
A personal project to monitor and analyze trending topics across social platforms
"""

import asyncio
import argparse
import signal
import sys
from datetime import datetime

from src.config import Config
from src.logger import setup_logging, get_logger
from src.twitter_client import TwitterClient
from src.reddit_client import RedditClient
from src.database import TrendDatabase, TrendRecord
from src.scheduler import TrendMonitorScheduler

# Setup logging
setup_logging()
logger = get_logger(__name__)


class TrendBot:
    def __init__(self):
        self.name = "TrendBot"
        self.version = "0.3.0"
        self.config = Config.from_env()
        self.scheduler = TrendMonitorScheduler(self.config)
        logger.info(f"Initializing {self.name} v{self.version}")

    async def test_connections(self):
        """Test all API connections"""
        print(f"🤖 {self.name} v{self.version} - Testing connections...")

        # Test Twitter
        print("\n📱 Testing Twitter API...")
        twitter_trends = await self.scheduler.twitter_client.get_trending_topics()
        if twitter_trends:
            print(f"✅ Found {len(twitter_trends)} Twitter trends")
            for trend in twitter_trends[:2]:
                print(f"  - {trend['name']}")
        else:
            print("⚠️  No Twitter trends found")

        # Test Reddit
        print("\n🔴 Testing Reddit API...")
        reddit_topics = await self.scheduler.reddit_client.get_hot_topics(['technology'], limit=3)
        if reddit_topics:
            print(f"✅ Found {len(reddit_topics)} Reddit hot topics")
            for topic in reddit_topics[:2]:
                print(f"  - r/{topic['subreddit']}: {topic['title'][:50]}...")
        else:
            print("⚠️  No Reddit topics found")

        # Test Telegram
        print("\n📨 Testing Telegram bot...")
        telegram_ok = await self.scheduler.telegram_notifier.test_connection()
        if telegram_ok:
            print("✅ Telegram bot connection successful")
        else:
            print("⚠️  Telegram bot connection failed")

        # Show database stats
        print("\n💾 Database status:")
        recent = self.scheduler.database.get_recent_trends(limit=5)
        print(f"  Recent trends: {len(recent)}")
        top_trends = self.scheduler.database.get_top_trends(limit=3)
        if top_trends:
            print("  Top trends:")
            for trend in top_trends:
                print(f"    - {trend['topic']} (score: {trend['max_score']})")

    async def run_monitor(self):
        """Start automated monitoring"""
        print(f"🤖 {self.name} v{self.version} - Starting automated monitoring...")
        print("Press Ctrl+C to stop")

        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Received shutdown signal, stopping...")
            self.scheduler.stop_monitoring()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            await self.scheduler.start_monitoring()
        except KeyboardInterrupt:
            print("👋 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            print(f"❌ Error: {e}")

    async def run_single_check(self):
        """Run a single monitoring check"""
        print(f"🤖 {self.name} v{self.version} - Single check mode")
        result = await self.scheduler.run_single_check()
        print(f"✅ Check completed: {result}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="TrendBot - Social Media Trend Monitor")
    parser.add_argument(
        'mode',
        choices=['test', 'monitor', 'check'],
        help='Mode to run: test (check connections), monitor (continuous), check (single run)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    # Setup logging with specified level
    setup_logging(log_level=args.log_level)

    bot = TrendBot()

    try:
        if args.mode == 'test':
            await bot.test_connections()
        elif args.mode == 'monitor':
            await bot.run_monitor()
        elif args.mode == 'check':
            await bot.run_single_check()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())