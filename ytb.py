import subprocess
import json
from datetime import datetime, timezone

CHANNELS = {
    "CNN Turk": "https://www.youtube.com/@cnnturk/live",
    "NTV Haber": "https://www.youtube.com/@NTV/live",
    "TGRT Haber": "https://www.youtube.com/@TGRTHaber/live",
    "Haber Global": "https://www.youtube.com/@HaberGlobal/live",
    "Haberturk": "https://www.youtube.com/@haberturk/live",
    "TV100": "https://www.youtube.com/@tv100/live",
    "Sozcu TV": "https://www.youtube.com/@sozcutv/live",
    "TRT Haber": "https://www.youtube.com/@TRTHaber/live",
}

def get_stream_url(channel_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "--no-playlist", "-g", channel_url],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip().splitlines()[0]
            return {"status": "ok", "url": url, "error": None}
        else:
            err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "No output"
            return {"status": "error", "url": None, "error": err}
    except subprocess.TimeoutExpired:
        return {"status": "error", "url": None, "error": "Timeout"}
    except FileNotFoundError:
        return {"status": "error", "url": None, "error": "yt-dlp not found"}
    except Exception as e:
        return {"status": "error", "url": None, "error": str(e)}


def main():
    print("Fetching stream URLs...", flush=True)
    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channels": {},
    }

    for name, url in CHANNELS.items():
        print(f"  -> {name} ... ", end="", flush=True)
        result = get_stream_url(url)
        output["channels"][name] = {
            "source_url": url,
            "stream_url": result["url"],
            "status": result["status"],
            "error": result["error"],
        }
        if result["status"] == "ok":
            print("OK")
        else:
            print(f"FAILED: {result['error']}")

    with open("ytb.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to ytb.json at {output['updated_at']}")


if __name__ == "__main__":
    main()
