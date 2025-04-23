"""
Data visualization and reporting functionality
"""

import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class TrendVisualizer:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up matplotlib style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10

    def create_trend_timeline(self, trend_data: List[Dict], topic: str) -> str:
        """Create a timeline chart for a specific trend"""
        if not trend_data:
            return None

        try:
            # Convert to DataFrame
            df = pd.DataFrame(trend_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

            # Create plot
            fig, ax = plt.subplots(figsize=(14, 8))

            # Plot trend line
            ax.plot(df['timestamp'], df['score'], linewidth=2, marker='o', markersize=4)

            # Formatting
            ax.set_title(f'Trend Timeline: {topic}', fontsize=16, fontweight='bold')
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Trend Score', fontsize=12)
            ax.grid(True, alpha=0.3)

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.xticks(rotation=45)

            # Add annotations for peak values
            max_score_idx = df['score'].idxmax()
            max_score = df.loc[max_score_idx, 'score']
            max_time = df.loc[max_score_idx, 'timestamp']

            ax.annotate(f'Peak: {max_score:.1f}',
                       xy=(max_time, max_score),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

            plt.tight_layout()

            # Save chart
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"trend_timeline_{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Created trend timeline chart: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error creating trend timeline: {e}")
            return None

    def create_platform_comparison(self, data_by_platform: Dict[str, List[Dict]]) -> str:
        """Create a comparison chart showing trends across platforms"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Platform Trend Comparison', fontsize=16, fontweight='bold')

            platforms = list(data_by_platform.keys())

            # 1. Trend count by platform (pie chart)
            ax1 = axes[0, 0]
            counts = [len(data_by_platform[platform]) for platform in platforms]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(platforms)]

            ax1.pie(counts, labels=platforms, autopct='%1.1f%%', colors=colors)
            ax1.set_title('Trend Distribution by Platform')

            # 2. Average scores by platform (bar chart)
            ax2 = axes[0, 1]
            avg_scores = []
            for platform in platforms:
                if data_by_platform[platform]:
                    avg_score = sum(item.get('score', 0) for item in data_by_platform[platform]) / len(data_by_platform[platform])
                    avg_scores.append(avg_score)
                else:
                    avg_scores.append(0)

            bars = ax2.bar(platforms, avg_scores, color=colors)
            ax2.set_title('Average Trend Scores by Platform')
            ax2.set_ylabel('Average Score')

            # Add value labels on bars
            for bar, score in zip(bars, avg_scores):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{score:.1f}', ha='center', va='bottom')

            # 3. Trend volume over time
            ax3 = axes[1, 0]
            for i, platform in enumerate(platforms):
                if not data_by_platform[platform]:
                    continue

                df = pd.DataFrame(data_by_platform[platform])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df_hourly = df.groupby(df['timestamp'].dt.floor('H')).size()

                ax3.plot(df_hourly.index, df_hourly.values,
                        label=platform, color=colors[i], linewidth=2)

            ax3.set_title('Trend Volume Over Time')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Number of Trends')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # 4. Top trending topics
            ax4 = axes[1, 1]
            all_topics = []
            for platform_data in data_by_platform.values():
                for item in platform_data:
                    all_topics.append((item.get('topic', ''), item.get('score', 0)))

            # Get top 10 topics by score
            top_topics = sorted(all_topics, key=lambda x: x[1], reverse=True)[:10]
            topic_names = [topic[0][:20] + '...' if len(topic[0]) > 20 else topic[0] for topic in top_topics]
            topic_scores = [topic[1] for topic in top_topics]

            bars = ax4.barh(range(len(topic_names)), topic_scores)
            ax4.set_yticks(range(len(topic_names)))
            ax4.set_yticklabels(topic_names)
            ax4.set_title('Top Trending Topics')
            ax4.set_xlabel('Score')

            plt.tight_layout()

            # Save chart
            filename = f"platform_comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Created platform comparison chart: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error creating platform comparison: {e}")
            return None

    def generate_daily_report(self, trends_data: List[Dict]) -> str:
        """Generate a daily trend report with key statistics"""
        try:
            report_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"daily_report_{report_date.replace('-', '')}.txt"
            filepath = os.path.join(self.output_dir, filename)

            if not trends_data:
                with open(filepath, 'w') as f:
                    f.write(f"Daily Trend Report - {report_date}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write("No trend data available for today.\n")
                return filepath

            # Analyze data
            df = pd.DataFrame(trends_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Statistics
            total_trends = len(df)
            unique_topics = df['topic'].nunique()
            platforms = df['platform'].unique()
            avg_score = df['score'].mean()
            top_score = df['score'].max()

            # Top trends by platform
            platform_stats = df.groupby('platform').agg({
                'score': ['count', 'mean', 'max'],
                'topic': 'nunique'
            }).round(2)

            # Top 10 trends overall
            top_trends = df.nlargest(10, 'score')[['topic', 'platform', 'score', 'timestamp']]

            # Write report
            with open(filepath, 'w') as f:
                f.write(f"Daily Trend Report - {report_date}\n")
                f.write("=" * 50 + "\n\n")

                f.write("SUMMARY\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total trends tracked: {total_trends}\n")
                f.write(f"Unique topics: {unique_topics}\n")
                f.write(f"Platforms monitored: {', '.join(platforms)}\n")
                f.write(f"Average trend score: {avg_score:.2f}\n")
                f.write(f"Highest trend score: {top_score:.2f}\n\n")

                f.write("PLATFORM BREAKDOWN\n")
                f.write("-" * 20 + "\n")
                for platform in platforms:
                    platform_data = df[df['platform'] == platform]
                    f.write(f"{platform.upper()}:\n")
                    f.write(f"  Trends: {len(platform_data)}\n")
                    f.write(f"  Avg Score: {platform_data['score'].mean():.2f}\n")
                    f.write(f"  Top Score: {platform_data['score'].max():.2f}\n\n")

                f.write("TOP TRENDS\n")
                f.write("-" * 20 + "\n")
                for i, (_, trend) in enumerate(top_trends.iterrows(), 1):
                    f.write(f"{i:2d}. {trend['topic'][:60]}\n")
                    f.write(f"     Platform: {trend['platform']} | Score: {trend['score']:.1f}\n")
                    f.write(f"     Time: {trend['timestamp'].strftime('%H:%M')}\n\n")

                f.write(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            logger.info(f"Generated daily report: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return None

    def create_keyword_cloud_data(self, trends_data: List[Dict]) -> Dict[str, int]:
        """Extract keyword frequency data for word cloud generation"""
        try:
            from collections import Counter
            import re

            all_words = []
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

            for trend in trends_data:
                topic = trend.get('topic', '') or trend.get('title', '')
                # Clean and tokenize
                words = re.findall(r'\b\w+\b', topic.lower())
                # Filter words
                filtered_words = [word for word in words
                                if len(word) > 2 and word not in stop_words]
                all_words.extend(filtered_words)

            word_freq = dict(Counter(all_words).most_common(50))
            logger.info(f"Generated keyword cloud data with {len(word_freq)} terms")
            return word_freq

        except Exception as e:
            logger.error(f"Error creating keyword cloud data: {e}")
            return {}