"""
IPTV Playlist Generator (link.json -> playlist.m3u + per-channel .m3u8)

This script:
  - Reads link.json (list of {"name": "...", "url": "..."})
  - Creates playlist/<name>.m3u8 for each channel
  - Creates playlist/playlist.m3u (IPTV M3U format)
  - Optionally pushes to GitHub

Requirements:
  pip install requests

Usage:
  python ytb.py

Input:
  link.json (in the same directory)

Output:
  playlist/<name>.m3u8
  playlist/playlist.m3u
"""

import json
import os
import time
from datetime import datetime

import requests

# GitHub repo settings (optional, for auto-push)
GITHUB_REPO = "tecotv2025/tecotv"  # "owner/repo"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # set via env var

BASE_URL = "https://raw.githubusercontent.com/"
RAW_BASE = f"{BASE_URL}{GITHUB_REPO}/{GITHUB_BRANCH}/playlist/"

PLAYLIST_DIR = "playlist"
LINK_JSON = "link.json"
MASTER_M3U = os.path.join(PLAYLIST_DIR, "playlist.m3u")


def ensure_dirs():
    os.makedirs(PLAYLIST_DIR, exist_ok=True)


def load_links():
    if not os.path.exists(LINK_JSON):
        print(f"Error: {LINK_JSON} not found.")
        exit(1)

    with open(LINK_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: link.json must be a list of objects.")
        exit(1)

    return data


def write_channel_m3u8(channel_name, stream_url):
    """Create per-channel .m3u8 file with HLS master playlist format."""
    safe_name = channel_name.replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}.m3u8"
    filepath = os.path.join(PLAYLIST_DIR, filename)

    content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def build_playlist_m3u(channels_files):
    """
    channels_files: list of (channel_name, filename, stream_url)
    Creates playlist/playlist.m3u
    """
    m3u_lines = ["#EXTM3U"]

    for name, filename, stream_url in channels_files:
        # GitHub Raw URL with timestamp to avoid cache
        raw_url = f"{RAW_BASE}{filename}?t={int(time.time())}"
        m3u_lines.append(f"#EXTINF:-1,{name}")
        m3u_lines.append(raw_url)

    with open(MASTER_M3U, "w", encoding="utf-8") as f:
        f.write("
".join(m3u_lines) + "
")


def git_push():
    """
    Optional: git add/commit/push using system git.
    Requires:
      - git installed
      - GITHUB_TOKEN set in environment
      - repo cloned locally with proper credentials
    """
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set, skipping Git push.")
        return

    import subprocess

    print(">>> Pushing to GitHub...")

    # Ensure we are on the correct branch
    subprocess.run(["git", "checkout", GITHUB_BRANCH], check=False)

    subprocess.run(["git", "add", "."], check=True)

    result = subprocess.run(
        ["git", "diff-index", "--quiet", "HEAD", "--"],
        capture_output=True,
    )

    if result.returncode != 0:
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
        commit_msg = f"Manifest Refresh: {timestamp}"

        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Use token in URL
        push_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
        subprocess.run(
            ["git", "push", push_url, f"HEAD:{GITHUB_BRANCH}", "--force"],
            check=True,
        )

        print(">>> Push to GitHub successful.")
    else:
        print(">>> No changes, skipping push.")


def main():
    print(">>> Loading channels from link.json...")
    links = load_links()

    ensure_dirs()

    channels_files = []

    print(">>> Processing channels...")
    for i, item in enumerate(links):
        name = item.get("name", "Unknown")
        url = item.get("url", "")

        if not url:
            print(f"[SKIP] {name}: no URL")
            continue

        print(f">>> {name}...")

        filename = write_channel_m3u8(name, url)
        channels_files.append((name, filename, url))
        print(f"   [OK] {name} -> playlist/{filename}")

        # Avoid overwhelming the server
        time.sleep(0.5)

    if not channels_files:
        print("Error: No channels processed.")
        exit(1)

    print(">>> Creating master playlist (playlist.m3u)...")
    build_playlist_m3u(channels_files)
    print(f"[OK] {MASTER_M3U} created.")

    print(">>> Pushing to GitHub...")
    git_push()

    print(">>> Done.")


if __name__ == "__main__":
    main()
