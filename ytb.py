"""
YouTube JSON to IPTV M3U Generator (with cookie support)

This script reads channel information from a YouTube live stream JSON,
uses streamlink and/or yt-dlp (with optional cookies) to extract m3u8/HLS
stream URLs, and generates a .m3u file compatible with IPTV players.

Requirements:
  pip install streamlink yt-dlp
  yt-dlp --cookies-from-browser chrome "https://www.youtube.com/@cnnturk/live" --cookies cookies.txt "https://www.youtube.com/@cnnturk/live"

Usage:
  python ytb.py

JSON file: channels.json (in the same directory)
Output: channels.m3u
Cookie file: cookies.txt (optional, in the same directory)
"""

import json
import os
import sys

try:
    import streamlink
    HAS_STREAMLINK = True
except ImportError:
    HAS_STREAMLINK = False

try:
    import yt_dlp
    HAS_YTDL = True
except ImportError:
    HAS_YTDL = False


def get_cookie_file():
    """
    Returns cookie file path if it exists.
    Looks for 'cookies.txt' in the current directory.
    """
    cookie_path = "cookies.txt"
    if os.path.exists(cookie_path):
        return cookie_path
    return None


def get_streamlink_stream_url(url, cookie_path=None):
    """Returns the best stream URL using streamlink."""
    if not HAS_STREAMLINK:
        return None
    try:
        streams = streamlink.streams(url)
        if not streams:
            return None
        best = streams.get("best")
        if best:
            return best.to_url()
    except Exception:
        return None
    return None


def get_ytdlp_stream_url(url, cookie_path=None):
    """Returns HLS/m3u8 URL using yt-dlp with optional cookie support."""
    if not HAS_YTDL:
        return None

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "format": "best",
        "dump_json": True,
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "url" in info:
                return info["url"]
            if "formats" in info:
                for f in info["formats"]:
                    if f.get("ext") == "m3u8" or f.get("format_note", "").lower() in ["hls", "dash"]:
                        if "url" in f:
                            return f["url"]
                best = None
                for f in info["formats"]:
                    if "url" in f:
                        best = f["url"]
                        break
                if best:
                    return best
    except Exception:
        pass
    return None


def get_stream_url(url):
    """
    Returns live stream URL (m3u8, etc.) from the given URL.
    Tries streamlink first, then yt-dlp with optional cookie.
    """
    cookie_path = get_cookie_file()

    stream_url = get_streamlink_stream_url(url, cookie_path)
    if stream_url:
        return stream_url

    stream_url = get_ytdlp_stream_url(url, cookie_path)
    if stream_url:
        return stream_url

    return None


def json_to_m3u(json_path="channels.json", m3u_path="channels.m3u"):
    """
    Reads JSON file, extracts channel info, and generates an M3U file.

    JSON structure:
    {
      "updated_at": "...",
      "channels": {
        "Channel Name": {
          "source_url": "https://...",
          "stream_url": "...",
          ...
        },
        ...
      }
    }
    """
    if not os.path.exists(json_path):
        print(f"Error: {json_path} file not found.")
        sys.exit(1)

    cookie_path = get_cookie_file()
    if cookie_path:
        print(f"Using cookie file: {cookie_path}")
    else:
        print("Warning: cookies.txt not found. YouTube streams may fail due to bot detection.")
        print("To create cookies.txt, run:")
        print('  yt-dlp --cookies-from-browser chrome "https://www.youtube.com/@cnnturk/live" --cookies cookies.txt "https://www.youtube.com/@cnnturk/live"')

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = data.get("channels", {})
    if not channels:
        print("Error: 'channels' field is empty or missing in JSON.")
        sys.exit(1)

    m3u_lines = ["#EXTM3U"]

    success_count = 0
    fail_count = 0

    for name, info in channels.items():
        source_url = info.get("source_url")
        existing_stream_url = info.get("stream_url")

        channel_name = name

        if existing_stream_url and existing_stream_url.startswith("http"):
            stream_url = existing_stream_url
        else:
            stream_url = None

        if not stream_url and source_url:
            stream_url = get_stream_url(source_url)

        if stream_url:
            m3u_lines.append(f"#EXTINF:-1,{channel_name}")
            m3u_lines.append(stream_url)
            success_count += 1
            print(f"[OK] {channel_name} -> {stream_url[:80]}...")
        else:
            fail_count += 1
            print(f"[ERROR] {channel_name} -> stream URL not found")

    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("
".join(m3u_lines) + "
")

    print(f"
{m3u_path} created.")
    print(f"Success: {success_count}, Failed: {fail_count}")


if __name__ == "__main__":
    json_path = "channels.json"
    m3u_path = "channels.m3u"

    json_to_m3u(json_path, m3u_path)
