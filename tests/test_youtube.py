import requests
import re
import urllib.parse

def find_youtube_video(query):
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=5)
    
    # Try videoId in initial JSON data
    match_json = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
    if match_json:
        return f"https://www.youtube.com/watch?v={match_json.group(1)}"
    
    # Try /watch?v= in HTML links
    match_html = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', resp.text)
    if match_html:
        return f"https://www.youtube.com/watch?v={match_html.group(1)}"
        
    return url

if __name__ == "__main__":
    from unittest.mock import patch
    response = type("Response", (), {"text": '"videoId":"abcdefghijk"'})()
    with patch("requests.get", return_value=response):
        link = find_youtube_video("Queen Bohemian Rhapsody")
    assert link == "https://www.youtube.com/watch?v=abcdefghijk", link
    print("PASS: YouTube result parsing (mocked; no network or browser launch)")
