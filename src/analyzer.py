"""
Trend analysis and scoring logic
"""

import logging
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrendScore:
    topic: str
    platform: str
    score: float
    velocity: float  # Rate of increase
    mentions: int
    peak_score: int
    first_seen: datetime
    last_seen: datetime


class TrendAnalyzer:
    def __init__(self):
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }

    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []

        # Clean text and convert to lowercase
        text = re.sub(r'[^\w\s#@]', ' ', text.lower())
        words = text.split()

        keywords = []
        for word in words:
            # Keep hashtags and mentions as-is
            if word.startswith('#') or word.startswith('@'):
                keywords.append(word)
            # Filter regular words
            elif (len(word) >= min_length and
                  word not in self.stop_words and
                  not word.isdigit()):
                keywords.append(word)

        return keywords

    def calculate_trend_score(self, topic_data: List[Dict]) -> float:
        """
        Calculate trend score based on multiple factors:
        - Engagement (likes, shares, comments)
        - Volume (number of mentions)
        - Velocity (rate of increase)
        - Recency (newer posts weighted higher)
        """
        if not topic_data:
            return 0.0

        total_score = 0.0
        total_weight = 0.0
        now = datetime.now()

        for item in topic_data:
            # Base engagement score
            engagement = 0
            if 'score' in item:  # Reddit
                engagement = item['score'] + item.get('num_comments', 0) * 2
            elif 'metrics' in item:  # Twitter
                metrics = item['metrics']
                engagement = (metrics.get('like_count', 0) +
                            metrics.get('retweet_count', 0) * 3 +
                            metrics.get('reply_count', 0) * 2)

            # Time decay factor (newer content weighted higher)
            time_diff = now - datetime.fromisoformat(str(item.get('created_at', now)))
            time_weight = max(0.1, 1.0 - (time_diff.total_seconds() / (24 * 3600)))

            # Platform weight
            platform_weight = 1.0
            if item.get('platform') == 'reddit':
                platform_weight = 0.8  # Reddit slightly less weighted

            weighted_score = engagement * time_weight * platform_weight
            total_score += weighted_score
            total_weight += time_weight

        # Normalize score
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.0

        # Apply logarithmic scaling to prevent extreme values
        import math
        final_score = math.log(normalized_score + 1) * 10

        return min(final_score, 100.0)  # Cap at 100

    def detect_emerging_trends(self, current_trends: List[Dict],
                             historical_data: List[Dict],
                             threshold: float = 2.0) -> List[TrendScore]:
        """Detect emerging trends by comparing current vs historical data"""

        emerging_trends = []

        # Group current trends by topic
        current_by_topic = {}
        for trend in current_trends:
            topic = trend.get('topic', '').lower()
            if topic not in current_by_topic:
                current_by_topic[topic] = []
            current_by_topic[topic].append(trend)

        # Group historical data
        historical_by_topic = {}
        cutoff_time = datetime.now() - timedelta(hours=24)

        for item in historical_data:
            if datetime.fromisoformat(str(item.get('timestamp', cutoff_time))) < cutoff_time:
                continue

            topic = item.get('topic', '').lower()
            if topic not in historical_by_topic:
                historical_by_topic[topic] = []
            historical_by_topic[topic].append(item)

        # Analyze each topic
        for topic, current_data in current_by_topic.items():
            if len(topic) < 3:  # Skip very short topics
                continue

            current_score = self.calculate_trend_score(current_data)
            historical_data_for_topic = historical_by_topic.get(topic, [])

            if not historical_data_for_topic:
                # New topic
                velocity = current_score
            else:
                historical_score = self.calculate_trend_score(historical_data_for_topic)
                velocity = current_score - historical_score

            # Check if it's emerging (significant increase)
            if velocity >= threshold:
                trend_score = TrendScore(
                    topic=topic,
                    platform=current_data[0].get('platform', 'unknown'),
                    score=current_score,
                    velocity=velocity,
                    mentions=len(current_data),
                    peak_score=max(item.get('score', 0) for item in current_data),
                    first_seen=min(datetime.fromisoformat(str(item.get('timestamp', datetime.now())))
                                 for item in current_data),
                    last_seen=max(datetime.fromisoformat(str(item.get('timestamp', datetime.now())))
                                for item in current_data)
                )
                emerging_trends.append(trend_score)

        # Sort by velocity (most emerging first)
        emerging_trends.sort(key=lambda x: x.velocity, reverse=True)

        logger.info(f"Detected {len(emerging_trends)} emerging trends")
        return emerging_trends

    def analyze_sentiment_keywords(self, trends: List[Dict]) -> Dict[str, int]:
        """Analyze common keywords and themes in trending topics"""

        all_keywords = []
        for trend in trends:
            title = trend.get('title', '') or trend.get('topic', '') or trend.get('name', '')
            keywords = self.extract_keywords(title)
            all_keywords.extend(keywords)

        # Count keyword frequency
        keyword_counter = Counter(all_keywords)

        # Remove very common but uninformative words
        filtered_keywords = {
            k: v for k, v in keyword_counter.items()
            if v > 1 and len(k) > 2
        }

        logger.info(f"Analyzed {len(all_keywords)} keywords, found {len(filtered_keywords)} significant ones")
        return dict(sorted(filtered_keywords.items(), key=lambda x: x[1], reverse=True))

    def generate_trend_summary(self, trends_by_platform: Dict[str, List[Dict]]) -> Dict:
        """Generate a comprehensive trend summary"""

        summary = {
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'top_keywords': {},
            'total_trends': 0
        }

        all_trends = []
        for platform, trends in trends_by_platform.items():
            if not trends:
                continue

            platform_summary = {
                'count': len(trends),
                'avg_score': sum(t.get('score', 0) for t in trends) / len(trends),
                'top_trend': max(trends, key=lambda x: x.get('score', 0)) if trends else None
            }

            summary['platforms'][platform] = platform_summary
            all_trends.extend(trends)

        summary['total_trends'] = len(all_trends)
        summary['top_keywords'] = self.analyze_sentiment_keywords(all_trends)

        return summary