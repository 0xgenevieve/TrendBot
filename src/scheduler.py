"""
Scheduler for automated trend monitoring and notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from src.config import Config
from src.twitter_client import TwitterClient
from src.reddit_client import RedditClient
from src.telegram_bot import TelegramNotifier
from src.database import TrendDatabase, TrendRecord
from src.analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class TrendMonitorScheduler:
    def __init__(self, config: Config):
        self.config = config
        self.twitter_client = TwitterClient(config.twitter)
        self.reddit_client = RedditClient(config.reddit)
        self.telegram_notifier = TelegramNotifier(config.telegram)
        self.database = TrendDatabase(config.database.db_path)
        self.analyzer = TrendAnalyzer()

        self.running = False
        self.last_check = None

        # Monitoring intervals (in minutes)
        self.twitter_interval = 30
        self.reddit_interval = 45
        self.notification_interval = 60
        self.daily_summary_hour = 20  # 8 PM

    async def start_monitoring(self):
        """Start the automated monitoring loop"""
        logger.info("Starting automated trend monitoring...")
        self.running = True

        # Schedule tasks
        tasks = [
            self._twitter_monitor_loop(),
            self._reddit_monitor_loop(),
            self._notification_loop(),
            self._daily_summary_loop()
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
        finally:
            self.running = False

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        logger.info("Stopping trend monitoring...")
        self.running = False

    async def _twitter_monitor_loop(self):
        """Monitor Twitter trends periodically"""
        while self.running:
            try:
                logger.info("Checking Twitter trends...")

                # Get trending topics
                trends = await self.twitter_client.get_trending_topics()

                if trends:
                    # Convert to TrendRecord format
                    records = []
                    timestamp = datetime.now()

                    for trend in trends:
                        record = TrendRecord(
                            platform='twitter',
                            topic=trend.get('name', ''),
                            score=trend.get('volume', 0),
                            volume=trend.get('volume'),
                            source_id=f"twitter_trend_{timestamp.strftime('%Y%m%d_%H%M')}",
                            metadata=json.dumps(trend),
                            timestamp=timestamp
                        )
                        records.append(record)

                    # Save to database
                    saved_count = self.database.save_trends_batch(records)
                    logger.info(f"Saved {saved_count} Twitter trends")

                else:
                    logger.warning("No Twitter trends retrieved")

            except Exception as e:
                logger.error(f"Twitter monitoring error: {e}")

            # Wait for next check
            await asyncio.sleep(self.twitter_interval * 60)

    async def _reddit_monitor_loop(self):
        """Monitor Reddit hot topics periodically"""
        while self.running:
            try:
                logger.info("Checking Reddit hot topics...")

                # Popular subreddits to monitor
                subreddits = ['technology', 'worldnews', 'politics', 'cryptocurrency',
                            'programming', 'artificial', 'MachineLearning']

                all_topics = await self.reddit_client.get_hot_topics(subreddits, limit=5)

                if all_topics:
                    records = []
                    timestamp = datetime.now()

                    for topic in all_topics:
                        record = TrendRecord(
                            platform='reddit',
                            topic=topic.get('title', ''),
                            score=topic.get('score', 0),
                            volume=topic.get('num_comments', 0),
                            source_id=topic.get('id', ''),
                            metadata=json.dumps({
                                'subreddit': topic.get('subreddit', ''),
                                'upvote_ratio': topic.get('upvote_ratio', 0),
                                'url': topic.get('url', ''),
                                'permalink': topic.get('permalink', '')
                            }),
                            timestamp=timestamp
                        )
                        records.append(record)

                    saved_count = self.database.save_trends_batch(records)
                    logger.info(f"Saved {saved_count} Reddit topics")

                else:
                    logger.warning("No Reddit topics retrieved")

            except Exception as e:
                logger.error(f"Reddit monitoring error: {e}")

            await asyncio.sleep(self.reddit_interval * 60)

    async def _notification_loop(self):
        """Send periodic notifications about emerging trends"""
        while self.running:
            try:
                # Wait initial period before first notification
                await asyncio.sleep(self.notification_interval * 60)

                logger.info("Analyzing trends for notifications...")

                # Get recent trends
                recent_trends = self.database.get_recent_trends(hours=2, limit=100)
                historical_trends = self.database.get_recent_trends(hours=24, limit=500)

                if recent_trends:
                    # Detect emerging trends
                    emerging = self.analyzer.detect_emerging_trends(
                        recent_trends, historical_trends, threshold=1.5
                    )

                    if emerging:
                        # Send notification for top emerging trends
                        top_emerging = emerging[:3]
                        message = "🚀 *Emerging Trends Alert*\n\n"

                        for i, trend in enumerate(top_emerging, 1):
                            message += f"{i}. *{trend.topic}* ({trend.platform})\n"
                            message += f"   Score: {trend.score:.1f} | Velocity: +{trend.velocity:.1f}\n"
                            message += f"   Mentions: {trend.mentions}\n\n"

                        message += f"_Detected at {datetime.now().strftime('%H:%M')}_"

                        await self.telegram_notifier.send_message(message)
                        logger.info(f"Sent emerging trends notification for {len(top_emerging)} trends")

            except Exception as e:
                logger.error(f"Notification loop error: {e}")

            await asyncio.sleep(self.notification_interval * 60)

    async def _daily_summary_loop(self):
        """Send daily summary at specified time"""
        while self.running:
            try:
                now = datetime.now()

                # Check if it's time for daily summary
                if now.hour == self.daily_summary_hour and now.minute < 5:
                    logger.info("Generating daily summary...")

                    # Get trends from last 24 hours
                    twitter_trends = self.database.get_recent_trends('twitter', hours=24, limit=100)
                    reddit_trends = self.database.get_recent_trends('reddit', hours=24, limit=100)

                    # Generate summary
                    trends_by_platform = {
                        'twitter': twitter_trends,
                        'reddit': reddit_trends
                    }

                    summary = self.analyzer.generate_trend_summary(trends_by_platform)

                    # Format summary data for Telegram
                    summary_data = {
                        'twitter': {
                            'count': len(twitter_trends),
                            'top_trend': twitter_trends[0]['topic'] if twitter_trends else None
                        },
                        'reddit': {
                            'count': len(reddit_trends),
                            'top_subreddit': self._get_top_subreddit(reddit_trends)
                        },
                        'total_records': summary['total_trends']
                    }

                    await self.telegram_notifier.send_daily_summary(summary_data)
                    logger.info("Daily summary sent")

                    # Sleep until next day to avoid multiple sends
                    await asyncio.sleep(3600)  # 1 hour

            except Exception as e:
                logger.error(f"Daily summary error: {e}")

            await asyncio.sleep(300)  # Check every 5 minutes

    def _get_top_subreddit(self, reddit_trends: List[Dict]) -> Optional[str]:
        """Extract the most active subreddit from Reddit trends"""
        if not reddit_trends:
            return None

        subreddit_counts = {}
        for trend in reddit_trends:
            try:
                metadata = json.loads(trend.get('metadata', '{}'))
                subreddit = metadata.get('subreddit', '')
                if subreddit:
                    subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
            except (json.JSONDecodeError, KeyError):
                continue

        if subreddit_counts:
            return max(subreddit_counts.items(), key=lambda x: x[1])[0]
        return None

    async def run_single_check(self):
        """Run a single monitoring check (useful for testing)"""
        logger.info("Running single trend check...")

        # Check Twitter
        twitter_trends = await self.twitter_client.get_trending_topics()
        logger.info(f"Twitter: {len(twitter_trends)} trends")

        # Check Reddit
        reddit_topics = await self.reddit_client.get_hot_topics(['technology'], limit=3)
        logger.info(f"Reddit: {len(reddit_topics)} topics")

        # Test Telegram
        await self.telegram_notifier.test_connection()

        return {
            'twitter_trends': len(twitter_trends),
            'reddit_topics': len(reddit_topics)
        }