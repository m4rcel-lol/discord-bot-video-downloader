"""Discord bot for downloading videos from public URLs using yt-dlp."""

import logging
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import discord
import requests
import yt_dlp
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

VIDEO_EXTENSIONS = {
    ".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("video-bot")


def _sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename, keeping it short."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(". ")
    if len(name) > 100:
        name = name[:100]
    return name or "video"


def _is_valid_url(url: str) -> bool:
    """Return True if *url* looks like a valid HTTP(S) URL."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def _has_video_extension(url: str) -> bool:
    """Return True if the URL path ends with a known video extension."""
    try:
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in VIDEO_EXTENSIONS)
    except Exception:
        return False


def _is_video_content_type(url: str) -> bool:
    """Return True if the URL's Content-Type header indicates video."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=10)
        content_type = resp.headers.get("Content-Type", "")
        return content_type.startswith("video/")
    except Exception:
        return False


def download_with_ytdlp(url: str, dest_dir: str) -> str | None:
    """Try to download using yt-dlp. Returns the file path or None."""
    output_template = os.path.join(dest_dir, "%(title).100s.%(ext)s")
    ydl_opts: dict = {
        "outtmpl": output_template,
        "format": (
            "bestvideo[filesize<{limit}]+bestaudio[filesize<{limit}]/"
            "best[filesize<{limit}]/bestvideo+bestaudio/best"
        ).format(limit=MAX_FILE_SIZE_BYTES),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return None
            filepath = ydl.prepare_filename(info)
            # yt-dlp may change the extension after merging
            if not os.path.exists(filepath):
                base, _ = os.path.splitext(filepath)
                filepath = base + ".mp4"
            if os.path.exists(filepath):
                return filepath
    except Exception as exc:
        logger.warning("yt-dlp failed for %s: %s", url, exc)
    return None


def download_direct(url: str, dest_dir: str) -> str | None:
    """Fallback: download the URL directly via HTTP if it looks like a video."""
    if not (_has_video_extension(url) or _is_video_content_type(url)):
        return None

    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        ext = ".mp4"
        if _has_video_extension(url):
            ext = os.path.splitext(urlparse(url).path)[1]
        elif "webm" in content_type:
            ext = ".webm"
        elif "matroska" in content_type or "x-matroska" in content_type:
            ext = ".mkv"

        filename = _sanitize_filename(f"video_{uuid.uuid4().hex[:8]}") + ext
        filepath = os.path.join(dest_dir, filename)

        size = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                size += len(chunk)
                if size > MAX_FILE_SIZE_BYTES:
                    f.close()
                    os.remove(filepath)
                    logger.warning("Direct download exceeded size limit for %s", url)
                    return None
                f.write(chunk)
        return filepath
    except Exception as exc:
        logger.warning("Direct download failed for %s: %s", url, exc)
    return None


def download_video(url: str, dest_dir: str) -> str | None:
    """Download a video: try yt-dlp first, then fall back to direct download."""
    os.makedirs(dest_dir, exist_ok=True)
    path = download_with_ytdlp(url, dest_dir)
    if path:
        return path
    return download_direct(url, dest_dir)


# ---------------------------------------------------------------------------
# Discord bot setup
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@tree.command(name="download", description="Download a video from a public URL")
@app_commands.describe(url="The public video URL to download")
async def download_command(interaction: discord.Interaction, url: str) -> None:
    if not _is_valid_url(url):
        await interaction.response.send_message(
            "❌ Please provide a valid HTTP or HTTPS URL.", ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)

    tmp_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR if os.path.isdir(DOWNLOAD_DIR) else None)
    try:
        filepath = await bot.loop.run_in_executor(None, download_video, url, tmp_dir)

        if filepath is None:
            await interaction.followup.send(
                "❌ Could not download a video from that URL. "
                "The site may not be supported or the video may be private.",
            )
            return

        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE_BYTES:
            await interaction.followup.send(
                f"❌ The downloaded video is too large to upload "
                f"({file_size / 1024 / 1024:.1f} MB, limit is {MAX_FILE_SIZE_MB} MB).",
            )
            return

        if file_size == 0:
            await interaction.followup.send("❌ The downloaded file is empty.")
            return

        filename = os.path.basename(filepath)
        await interaction.followup.send(
            content=f"✅ Here is your video from <{url}>:",
            file=discord.File(filepath, filename=filename),
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@bot.event
async def on_ready() -> None:
    await tree.sync()
    logger.info("Bot is ready as %s (ID: %s)", bot.user, bot.user.id if bot.user else "?")


def main() -> None:
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN environment variable is not set. See .env.example.")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    bot.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
