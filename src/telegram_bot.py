"""
Telegram bot client for sending trend notifications
"""

import logging
import asyncio
from typing import List, Dict, Optional
from telegram import Bot
from telegram.constants import ParseMode
from src.config import TelegramConfig

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.bot = None
        self._setup_bot()

    def _setup_bot(self):
        """Initialize Telegram bot"""
        if not self.config.bot_token:
            logger.warning("Telegram bot token not provided")
            return

        try:
            self.bot = Bot(token=self.config.bot_token)
            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")

    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """Send a message to Telegram chat"""
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False

        target_chat_id = chat_id or self.config.chat_id
        if not target_chat_id:
            logger.error("No chat ID provided")
            return False

        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Message sent to Telegram chat {target_chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_trend_alert(self, trends: List[Dict], platform: str) -> bool:
        """Send a formatted trend alert"""
        if not trends:
            return False

        try:
            message = f"🔥 *Trending on {platform.capitalize()}*\n\n"

            for i, trend in enumerate(trends[:5], 1):
                if platform == 'twitter':
                    message += f"{i}. `{trend.get('name', 'Unknown')}` (vol: {trend.get('volume', 'N/A')})\n"
                elif platform == 'reddit':
                    score = trend.get('score', 0)
                    subreddit = trend.get('subreddit', 'Unknown')
                    title = trend.get('title', 'Unknown')[:60]
                    message += f"{i}. r/{subreddit}: *{title}...* (⬆️{score})\n"

            message += f"\n📊 Total trends: {len(trends)}"
            message += f"\n🕐 {asyncio.get_event_loop().time()}"

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send trend alert: {e}")
            return False

    async def send_daily_summary(self, summary_data: Dict) -> bool:
        """Send daily trending summary"""
        try:
            message = "📈 *Daily Trend Summary*\n\n"

            if 'twitter' in summary_data:
                twitter_data = summary_data['twitter']
                message += f"📱 *Twitter*: {twitter_data.get('count', 0)} trends tracked\n"
                if twitter_data.get('top_trend'):
                    message += f"   Top: `{twitter_data['top_trend']}`\n"

            if 'reddit' in summary_data:
                reddit_data = summary_data['reddit']
                message += f"🔴 *Reddit*: {reddit_data.get('count', 0)} hot topics\n"
                if reddit_data.get('top_subreddit'):
                    message += f"   Most active: r/{reddit_data['top_subreddit']}\n"

            message += f"\n💾 Total records: {summary_data.get('total_records', 0)}"
            message += "\n\n_Powered by TrendBot_ 🤖"

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test the Telegram bot connection"""
        if not self.bot:
            return False

        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{bot_info.username}")

            # Send test message if chat_id is configured
            if self.config.chat_id:
                test_msg = "🤖 TrendBot test message - connection successful!"
                await self.send_message(test_msg)

            return True

        except Exception as e:
            logger.error(f"Telegram bot connection test failed: {e}")
            return False