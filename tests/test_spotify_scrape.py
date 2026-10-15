import requests
import re
import urllib.parse
from unittest.mock import patch

def find_spotify_track(query):
    search_q = f"{query} site:open.spotify.com/track"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_q)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        matches = re.findall(r"open\.spotify\.com/track/([a-zA-Z0-9]+)", r.text)
        return matches
    except Exception as e:
        print("Error:", e)
        return []

if __name__ == "__main__":
    fake_response = type("Response", (), {"text": "open.spotify.com/track/AbC123xyz"})()
    with patch("requests.get", return_value=fake_response):
        for query in ("starboy the weeknd", "believer imagine dragons", "kesariya arijit singh"):
            tracks = find_spotify_track(query)
            assert tracks == ["AbC123xyz"], f"Unexpected parsed tracks: {tracks}"
    print("PASS: Spotify search result parsing (mocked; no network or playback)")
