"""
Configuration management for TrendBot
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TwitterConfig:
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_token_secret: Optional[str] = None
    bearer_token: Optional[str] = None


@dataclass
class RedditConfig:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    user_agent: str = "TrendBot/1.0"


@dataclass
class TelegramConfig:
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


@dataclass
class DatabaseConfig:
    db_path: str = "data/trends.db"


@dataclass
class Config:
    twitter: TwitterConfig
    reddit: RedditConfig
    telegram: TelegramConfig
    database: DatabaseConfig

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            twitter=TwitterConfig(
                api_key=os.getenv('TWITTER_API_KEY'),
                api_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
            ),
            reddit=RedditConfig(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'TrendBot/1.0')
            ),
            telegram=TelegramConfig(
                bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
                chat_id=os.getenv('TELEGRAM_CHAT_ID')
            ),
            database=DatabaseConfig(
                db_path=os.getenv('DATABASE_PATH', 'data/trends.db')
            )
        )