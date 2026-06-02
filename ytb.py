import json
import os
import time

PLAYLIST_DIR = "playlist"
LINK_JSON = "link.json"
MASTER_M3U = os.path.join(PLAYLIST_DIR, "playlist.m3u")

GITHUB_REPO = "Greenasaf/ytbjournal"
GITHUB_BRANCH = "main"
RAW_BASE = (
    "https://raw.githubusercontent.com/"
    + GITHUB_REPO
    + "/"
    + GITHUB_BRANCH
    + "/playlist/"
)


def ensure_dirs():
    os.makedirs(PLAYLIST_DIR, exist_ok=True)


def load_links():
    if not os.path.exists(LINK_JSON):
        print("Error: " + LINK_JSON + " not found.")
        exit(1)

    with open(LINK_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: link.json must be a list of objects.")
        exit(1)

    return data


def write_channel_m3u8(channel_name, stream_url):
    safe_name = channel_name.replace("/", "_").replace("\\", "_")
    filename = safe_name + ".m3u8"
    filepath = os.path.join(PLAYLIST_DIR, filename)

    header = "#EXTM3U
"
    header += "#EXT-X-VERSION:3
"
    header += "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
"

    content = header + stream_url + "
"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def build_playlist_m3u(channels_files):
    m3u_lines = ["#EXTM3U"]

    for name, filename, stream_url in channels_files:
        raw_url = RAW_BASE + filename + "?t=" + str(int(time.time()))
        m3u_lines.append("#EXTINF:-1," + name)
        m3u_lines.append(raw_url)

    with open(MASTER_M3U, "w", encoding="utf-8") as f:
        f.write("
".join(m3u_lines) + "
")


def main():
    print(">>> Loading channels from link.json...")
    links = load_links()

    ensure_dirs()

    channels_files = []

    print(">>> Processing channels...")
    for item in links:
        name = item.get("name", "Unknown")
        url = item.get("url", "")

        if not url:
            print("[SKIP] " + name + ": no URL")
            continue

        print(">>> " + name + "...")

        filename = write_channel_m3u8(name, url)
        channels_files.append((name, filename, url))
        print("   [OK] " + name + " -> playlist/" + filename)

        time.sleep(0.3)

    if not channels_files:
        print("Error: No channels processed.")
        exit(1)

    print(">>> Creating master playlist (playlist.m3u)...")
    build_playlist_m3u(channels_files)
    print("[OK] " + MASTER_M3U + " created.")

    print(">>> Done.")


if __name__ == "__main__":
    main()
