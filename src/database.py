"""
Database models and operations for storing trend data
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrendRecord:
    platform: str  # 'twitter', 'reddit'
    topic: str
    score: int
    volume: Optional[int]
    source_id: str
    metadata: str  # JSON string for additional data
    timestamp: datetime
    id: Optional[int] = None


class TrendDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create trends table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        volume INTEGER,
                        source_id TEXT,
                        metadata TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create index for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_platform_timestamp
                    ON trends(platform, timestamp)
                ''')

                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_topic_timestamp
                    ON trends(topic, timestamp)
                ''')

                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def save_trend(self, trend: TrendRecord) -> bool:
        """Save a single trend record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trends (platform, topic, score, volume, source_id, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend.platform,
                    trend.topic,
                    trend.score,
                    trend.volume,
                    trend.source_id,
                    trend.metadata,
                    trend.timestamp
                ))
                conn.commit()
                logger.debug(f"Saved trend: {trend.topic} from {trend.platform}")
                return True

        except Exception as e:
            logger.error(f"Failed to save trend: {e}")
            return False

    def save_trends_batch(self, trends: List[TrendRecord]) -> int:
        """Save multiple trend records in batch"""
        saved_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                trend_data = [
                    (t.platform, t.topic, t.score, t.volume, t.source_id, t.metadata, t.timestamp)
                    for t in trends
                ]

                cursor.executemany('''
                    INSERT INTO trends (platform, topic, score, volume, source_id, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', trend_data)

                saved_count = cursor.rowcount
                conn.commit()
                logger.info(f"Saved {saved_count} trends to database")

        except Exception as e:
            logger.error(f"Failed to save trends batch: {e}")

        return saved_count

    def get_recent_trends(self, platform: str = None, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent trends from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT platform, topic, score, volume, source_id, metadata, timestamp
                    FROM trends
                    WHERE datetime(timestamp) > datetime('now', '-{} hours')
                '''.format(hours)

                params = []
                if platform:
                    query += ' AND platform = ?'
                    params.append(platform)

                query += ' ORDER BY timestamp DESC, score DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                trends = []
                for row in rows:
                    trends.append({
                        'platform': row[0],
                        'topic': row[1],
                        'score': row[2],
                        'volume': row[3],
                        'source_id': row[4],
                        'metadata': row[5],
                        'timestamp': row[6]
                    })

                logger.info(f"Retrieved {len(trends)} recent trends")
                return trends

        except Exception as e:
            logger.error(f"Failed to get recent trends: {e}")
            return []

    def get_top_trends(self, platform: str = None, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get top trending topics by score"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT topic, platform, MAX(score) as max_score, COUNT(*) as mentions
                    FROM trends
                    WHERE datetime(timestamp) > datetime('now', '-{} hours')
                '''.format(hours)

                params = []
                if platform:
                    query += ' AND platform = ?'
                    params.append(platform)

                query += '''
                    GROUP BY topic, platform
                    ORDER BY max_score DESC, mentions DESC
                    LIMIT ?
                '''
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                trends = []
                for row in rows:
                    trends.append({
                        'topic': row[0],
                        'platform': row[1],
                        'max_score': row[2],
                        'mentions': row[3]
                    })

                logger.info(f"Retrieved {len(trends)} top trends")
                return trends

        except Exception as e:
            logger.error(f"Failed to get top trends: {e}")
            return []