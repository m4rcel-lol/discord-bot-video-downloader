# Discord Bot – Video Downloader

A Discord bot that downloads videos from virtually any public URL using **yt-dlp** (1 000+ supported sites) with an automatic direct-download fallback.

## Features

- **`/download url:`** slash command – paste any public video URL
- **yt-dlp** as the primary engine (YouTube, TikTok, Instagram, Twitter/X, Reddit, Vimeo, Facebook, Twitch, and many more)
- **Direct-download fallback** – if yt-dlp cannot handle the URL, the bot tries a plain HTTP download when the URL points to a video file or serves a `video/*` Content-Type
- Automatic file-size check against Discord's upload limit

## Requirements

- Python 3.11+
- A Discord bot token ([create one here](https://discord.com/developers/applications))

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/m4rcel-lol/discord-bot-video-downloader.git
cd discord-bot-video-downloader

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env and set DISCORD_TOKEN

# 4. Run the bot
python bot.py
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DISCORD_TOKEN` | *(required)* | Your Discord bot token |
| `MAX_FILE_SIZE_MB` | `25` | Maximum video file size in MB for uploads |
| `DOWNLOAD_DIR` | `downloads` | Temporary download directory |

## Running Tests

```bash
pip install pytest
pytest tests/
```
