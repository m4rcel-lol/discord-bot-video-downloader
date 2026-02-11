"""Unit tests for bot helper functions and download logic."""

import os
import tempfile
from unittest import mock

import pytest

from bot import (
    _has_video_extension,
    _is_valid_url,
    _sanitize_filename,
    check_ffmpeg,
    download_direct,
    download_with_ytdlp,
    download_video,
)


# ---------------------------------------------------------------------------
# check_ffmpeg
# ---------------------------------------------------------------------------

class TestCheckFfmpeg:
    def test_returns_path_when_found(self):
        with mock.patch("bot.shutil.which", return_value="/usr/bin/ffmpeg"):
            assert check_ffmpeg() == "/usr/bin/ffmpeg"

    def test_returns_none_when_not_found(self):
        with mock.patch("bot.shutil.which", return_value=None):
            assert check_ffmpeg() is None


# ---------------------------------------------------------------------------
# _is_valid_url
# ---------------------------------------------------------------------------

class TestIsValidUrl:
    def test_valid_https(self):
        assert _is_valid_url("https://www.youtube.com/watch?v=abc") is True

    def test_valid_http(self):
        assert _is_valid_url("http://example.com/video.mp4") is True

    def test_missing_scheme(self):
        assert _is_valid_url("www.youtube.com/watch?v=abc") is False

    def test_ftp_scheme(self):
        assert _is_valid_url("ftp://files.example.com/video.mp4") is False

    def test_empty_string(self):
        assert _is_valid_url("") is False

    def test_random_text(self):
        assert _is_valid_url("not a url at all") is False


# ---------------------------------------------------------------------------
# _has_video_extension
# ---------------------------------------------------------------------------

class TestHasVideoExtension:
    def test_mp4(self):
        assert _has_video_extension("https://example.com/file.mp4") is True

    def test_webm(self):
        assert _has_video_extension("https://example.com/file.webm") is True

    def test_mkv(self):
        assert _has_video_extension("https://example.com/file.mkv") is True

    def test_non_video(self):
        assert _has_video_extension("https://example.com/file.txt") is False

    def test_no_extension(self):
        assert _has_video_extension("https://example.com/watch?v=abc") is False


# ---------------------------------------------------------------------------
# _sanitize_filename
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_clean_name(self):
        assert _sanitize_filename("my_video") == "my_video"

    def test_special_chars(self):
        result = _sanitize_filename('file<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result

    def test_long_name(self):
        result = _sanitize_filename("a" * 200)
        assert len(result) <= 100

    def test_empty_name(self):
        assert _sanitize_filename("") == "video"

    def test_dots_only(self):
        assert _sanitize_filename("...") == "video"


# ---------------------------------------------------------------------------
# download_with_ytdlp (mocked)
# ---------------------------------------------------------------------------

class TestDownloadWithYtdlp:
    def test_success(self, tmp_path):
        fake_file = tmp_path / "My Video.mp4"
        fake_file.write_bytes(b"\x00" * 100)

        fake_info = {"title": "My Video", "ext": "mp4"}
        mock_ydl = mock.MagicMock()
        mock_ydl.extract_info.return_value = fake_info
        mock_ydl.prepare_filename.return_value = str(fake_file)
        mock_ydl.__enter__ = mock.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("bot.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_with_ytdlp("https://example.com/v", str(tmp_path))
        assert result == str(fake_file)

    def test_returns_none_on_exception(self, tmp_path):
        with mock.patch("bot.yt_dlp.YoutubeDL", side_effect=Exception("fail")):
            result = download_with_ytdlp("https://example.com/v", str(tmp_path))
        assert result is None

    def test_passes_ffmpeg_location_when_set(self, tmp_path):
        import bot as bot_module

        fake_file = tmp_path / "My Video.mp4"
        fake_file.write_bytes(b"\x00" * 100)

        fake_info = {"title": "My Video", "ext": "mp4"}
        mock_ydl = mock.MagicMock()
        mock_ydl.extract_info.return_value = fake_info
        mock_ydl.prepare_filename.return_value = str(fake_file)
        mock_ydl.__enter__ = mock.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch.object(bot_module, "_ffmpeg_location", "/usr/bin/ffmpeg"), \
             mock.patch("bot.yt_dlp.YoutubeDL", return_value=mock_ydl) as mock_cls:
            download_with_ytdlp("https://example.com/v", str(tmp_path))
        opts = mock_cls.call_args[0][0]
        assert opts["ffmpeg_location"] == "/usr/bin/ffmpeg"


# ---------------------------------------------------------------------------
# download_direct (mocked)
# ---------------------------------------------------------------------------

class TestDownloadDirect:
    def test_downloads_video_url(self, tmp_path):
        fake_resp = mock.MagicMock()
        fake_resp.headers = {"Content-Type": "video/mp4"}
        fake_resp.iter_content.return_value = [b"\x00" * 100]
        fake_resp.raise_for_status = mock.MagicMock()

        with mock.patch("bot.requests.get", return_value=fake_resp), \
             mock.patch("bot._has_video_extension", return_value=True), \
             mock.patch("bot._is_video_content_type", return_value=False):
            result = download_direct("https://example.com/file.mp4", str(tmp_path))
        assert result is not None
        assert os.path.exists(result)

    def test_returns_none_for_non_video(self, tmp_path):
        with mock.patch("bot._has_video_extension", return_value=False), \
             mock.patch("bot._is_video_content_type", return_value=False):
            result = download_direct("https://example.com/page", str(tmp_path))
        assert result is None


# ---------------------------------------------------------------------------
# download_video (integration of both methods, mocked)
# ---------------------------------------------------------------------------

class TestDownloadVideo:
    def test_ytdlp_success_skips_fallback(self, tmp_path):
        with mock.patch("bot.download_with_ytdlp", return_value="/tmp/fake.mp4") as m_yt, \
             mock.patch("bot.download_direct") as m_direct:
            result = download_video("https://example.com/v", str(tmp_path))
        assert result == "/tmp/fake.mp4"
        m_yt.assert_called_once()
        m_direct.assert_not_called()

    def test_falls_back_to_direct(self, tmp_path):
        with mock.patch("bot.download_with_ytdlp", return_value=None), \
             mock.patch("bot.download_direct", return_value="/tmp/direct.mp4") as m_direct:
            result = download_video("https://example.com/file.mp4", str(tmp_path))
        assert result == "/tmp/direct.mp4"
        m_direct.assert_called_once()

    def test_both_fail(self, tmp_path):
        with mock.patch("bot.download_with_ytdlp", return_value=None), \
             mock.patch("bot.download_direct", return_value=None):
            result = download_video("https://example.com/v", str(tmp_path))
        assert result is None
