# TrendBot 🤖

A personal project for monitoring and analyzing trending topics across social media platforms like Twitter and Reddit. TrendBot automatically tracks trends, analyzes their growth patterns, and sends notifications about emerging topics.

## Features

- **Multi-Platform Monitoring**: Track trends from Twitter and Reddit
- **Intelligent Analysis**: Score trends based on engagement, velocity, and recency
- **Emerging Trend Detection**: Identify rapidly growing topics before they peak
- **Telegram Notifications**: Get alerts about hot trends and daily summaries
- **SQLite Database**: Store and analyze historical trend data
- **Automated Scheduling**: Run continuous monitoring in the background

## Quick Start

1. **Clone and install dependencies**:
   ```bash
   git clone <repository-url>
   cd TrendBot
   pip install -r requirements.txt
   ```

2. **Configure API credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Test connections**:
   ```bash
   python main.py test
   ```

4. **Start monitoring**:
   ```bash
   python main.py monitor
   ```

## Configuration

Copy `.env.example` to `.env` and configure:

### Twitter API
- Get credentials from [Twitter Developer Portal](https://developer.twitter.com/)
- Set `TWITTER_BEARER_TOKEN` (minimum required)

### Reddit API
- Create an app at [Reddit Apps](https://www.reddit.com/prefs/apps)
- Set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`

### Telegram Bot
- Create a bot with [@BotFather](https://t.me/BotFather)
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## Usage

### Modes

- `test` - Check API connections and configuration
- `monitor` - Run continuous monitoring (press Ctrl+C to stop)
- `check` - Perform a single trend check

### Examples

```bash
# Test all integrations
python main.py test

# Start automated monitoring
python main.py monitor

# Quick trend check
python main.py check

# Debug mode
python main.py test --log-level DEBUG
```

## How It Works

1. **Data Collection**: Fetches trending topics from Twitter and hot posts from Reddit subreddits
2. **Storage**: Saves trend data to SQLite database with timestamps and metadata
3. **Analysis**: Calculates trend scores based on engagement metrics and growth velocity
4. **Detection**: Identifies emerging trends by comparing current vs historical data
5. **Notifications**: Sends Telegram alerts for significant trend changes and daily summaries

## Project Structure

```
TrendBot/
├── main.py              # Entry point with CLI
├── requirements.txt     # Dependencies
├── .env.example        # Configuration template
├── src/
│   ├── config.py       # Configuration management
│   ├── twitter_client.py # Twitter API integration
│   ├── reddit_client.py  # Reddit API integration
│   ├── telegram_bot.py   # Telegram notifications
│   ├── database.py      # SQLite database models
│   ├── analyzer.py      # Trend scoring and analysis
│   ├── scheduler.py     # Automated monitoring
│   └── logger.py        # Logging configuration
├── data/               # Database storage
└── logs/               # Application logs
```

## Monitoring Schedule

- **Twitter**: Check every 30 minutes
- **Reddit**: Check every 45 minutes
- **Notifications**: Send emerging trend alerts hourly
- **Daily Summary**: Send at 8 PM with day's highlights

## Contributing

This is a personal learning project, but feel free to fork and adapt for your own use!

## License

MIT License - see LICENSE file for details