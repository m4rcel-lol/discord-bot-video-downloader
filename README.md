# Discord Bot – Video Downloader

A Discord bot that downloads videos from virtually any public URL using **yt-dlp** (1,000+ supported sites) with an automatic direct-download fallback.

## Features

- **`/download url:`** slash command – paste any public video URL
- **yt-dlp** as the primary engine (YouTube, TikTok, Instagram, Twitter/X, Reddit, Vimeo, Facebook, Twitch, and many more)
- **Direct-download fallback** – if yt-dlp cannot handle the URL, the bot tries a plain HTTP download when the URL points to a video file or serves a `video/*` Content-Type
- Automatic file-size check against Discord's upload limit

## Requirements

- Python 3.11+
- A Discord bot token ([create one here](https://discord.com/developers/applications))

---

## Windows Setup (Testing)

Use the provided batch scripts to get started quickly on Windows:

```bat
REM 1. Clone the repository
git clone https://github.com/m4rcel-lol/discord-bot-video-downloader.git
cd discord-bot-video-downloader

REM 2. Run the setup script (creates venv, installs deps, creates .env)
setup.bat

REM 3. Edit .env and set your DISCORD_TOKEN

REM 4. Start the bot
start.bat

REM 5. Run tests
run_tests.bat
```

### Available batch scripts

| Script | Description |
|---|---|
| `setup.bat` | Creates a virtual environment, installs dependencies, and copies `.env.example` to `.env` |
| `start.bat` | Activates the venv and runs the bot |
| `run_tests.bat` | Activates the venv and runs the test suite with pytest |

---

## Linux / macOS Setup

```bash
# 1. Clone the repository
git clone https://github.com/m4rcel-lol/discord-bot-video-downloader.git
cd discord-bot-video-downloader

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env and set DISCORD_TOKEN

# 4. Run the bot
python bot.py
```

---

## Docker Deployment (Alpine Linux)

Deploy to an Alpine Linux server using Docker:

```bash
# 1. Clone the repository on your server
git clone https://github.com/m4rcel-lol/discord-bot-video-downloader.git
cd discord-bot-video-downloader

# 2. Configure
cp .env.example .env
# Edit .env and set DISCORD_TOKEN

# 3. Build and start with Docker Compose
docker compose up -d

# View logs
docker compose logs -f

# Stop the bot
docker compose down
```

Or build and run manually:

```bash
docker build -t discord-video-bot .
docker run -d --env-file .env --name discord-video-bot discord-video-bot
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
