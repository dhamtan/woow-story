import os
import json
import requests
import feedparser
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from tmdbv3api import TMDb, Movie

# ------------- ENV + CONSTANTS -------------

GEMINI_KEY = os.getenv("GEMINI_KEY")
PEXELS_KEY = os.getenv("PEXELS_KEY")
TMDB_KEY = os.getenv("TMDB_KEY")
SITE_URL = os.getenv("MY_URL")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

JSON_FILE = "service_account.json"

# ------------- SAFETY CHECKS -------------

if not GEMINI_KEY or not PEXELS_KEY or not TMDB_KEY or not SITE_URL or not GOOGLE_SERVICE_ACCOUNT_JSON:
    raise RuntimeError("One or more required environment variables are missing. Check GitHub Secrets.")

# Service account JSON ko file me likhna (Indexing API ke liye)
try:
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        f.write(GOOGLE_SERVICE_ACCOUNT_JSON)
except Exception as e:
    raise RuntimeError(f"Failed to write service_account.json: {e}")

# TMDB Setup
tmdb = TMDb()
tmdb.api_key = TMDB_KEY
movie = Movie()

# ------------- TOPIC FETCH -------------

def get_viral_topics():
    # India trend (Hindi) – yaha aap baad me koi specific RSS / API laga sakte hain
    try:
        in_feed = feedparser.parse("https://news.google.com/rss?hl=hi-IN&gl=IN&ceid=IN:hi")
        topic_hi = in_feed.entries[0].title if in_feed.entries else "Aaj ka sabse bada India trend"
    except Exception:
        topic_hi = "Aaj ka sabse bada India trend"

    # Global movie trend (English)
    try:
        popular_movies = movie.popular()
        topic_en = popular_movies[0].title if popular_movies else "Global cinema trending today"
    except Exception:
        topic_en = "Global entertainment breaking update"

    return topic_hi, topic_en

# ------------- GEMINI CONTENT -------------

def generate_content(topic, lang):
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-pro")

        prompt = (
            f"Write a 5-slide viral Google Web Story on '{topic}' in {lang}. "
            f"Slide 1 must be a suspenseful hook. "
            f"Maximum 10 words per slide. "
            f"Return ONLY in this exact format (no extra text): "
            f"""Slide 1: text
Slide 2: text
Slide 3: text
Slide 4: text
Slide 5: text""""
        )

        response = model.generate_content(prompt)
        text = response.text.strip() if response and response.text else ""
        if not text:
            raise ValueError("Empty Gemini response")
        return text
    except Exception as e:
        print(f"Gemini Error ({lang}): {e}")
        return (
            "Slide 1: Breaking update you must see now
"
            "Slide 2: Latest trend reshaping India and world
"
            "Slide 3: Hidden story behind big headlines
"
            "Slide 4: Key facts in simple words
"
            "Slide 5: Stay tuned for next update"
        )

# ------------- IMAGE FETCH (PEXELS) -------------

def get_hd_image(query):
    # Pexels official: https://api.pexels.com/v1/search?query=... [web:10]
    base = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "portrait"
    }
    headers = {"Authorization": PEXELS_KEY}

    try:
        r = requests.get(base, headers=headers, params=params, timeout=15)
        data = r.json()
        if "photos" in data and data["photos"]:
            return data["photos"][0]["src"]["large2x"]
    except Exception as e:
        print(f"Pexels Error: {e}")

    # Fallback image (safe generic)
    return "https://images.pexels.com/photos/261187/pexels-photo-261187.jpeg"

# ------------- AMP STORY HTML -------------

def parse_slides(raw):
    slides = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            parts = line.split(":", 1)
            text = parts[1].strip()
        else:
            text = line
        if text:
            slides.append(text)
    # exactly 5 slides chahiye
    while len(slides) < 5:
        slides.append("More details coming soon")
    return slides[:5]

def build_story_html(title, slides, img, canonical, lang_code):
    # Slide 1: hook, Slide 2-5: rest
    hook = slides[0]
    others = slides[1:]

    story_id_prefix = "story-" + lang_code

    html = f"""<!doctype html>
<html amp lang="{lang_code}">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="canonical" href="{canonical}">
  <meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1">
  <script async src="https://cdn.ampproject.org/v0.js"></script>
  <script async custom-element="amp-story" src="https://cdn.ampproject.org/v0/amp-story-1.0.js"></script>
  <style amp-boilerplate>
    body{{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;
    -moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;
    -ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;
    animation:-amp-start 8s steps(1,end) 0s 1 normal both}}
    @-webkit-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}
    @keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}
  </style>
  <noscript>
    <style amp-boilerplate>
      body{{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}}
    </style>
  </noscript>
</head>
<body>
  <amp-story standalone
    title="{title}"
    publisher="AutoBot"
    publisher-logo-src="logo.png"
    poster-portrait-src="{img}">
    
    <amp-story-page id="{story_id_prefix}-p1">
      <amp-story-grid-layer template="fill">
        <amp-img src="{img}" width="720" height="1280" layout="responsive"></amp-img>
      </amp-story-grid-layer>
      <amp-story-grid-layer template="vertical">
        <h1>{hook}</h1>
      </amp-story-grid-layer>
    </amp-story-page>
"""

    # remaining slides
    for i, text in enumerate(others, start=2):
        html += f"""
    <amp-story-page id="{story_id_prefix}-p{i}">
      <amp-story-grid-layer template="vertical">
        <div style="background:rgba(0,0,0,0.65);padding:16px;color:#fff;font-size:24px;line-height:1.4;">
          {text}
        </div>
      </amp-story-grid-layer>
    </amp-story-page>
"""

    html += """
  </amp-story>
</body>
</html>
"""
    return html

def save_html(filename, html):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

# ------------- GOOGLE INDEXING API -------------

def push_to_google(url):
    try:
        scopes = ["https://www.googleapis.com/auth/indexing"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scopes=scopes)
        token = creds.get_access_token().access_token

        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        payload = {"url": url, "type": "URL_UPDATED"}  # [web:8]

        r = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        print(f"Index push {url} -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"Indexing Error for {url}: {e}")

# ------------- MAIN -------------

def main():
    topic_hi, topic_en = get_viral_topics()
    print("Topics:", topic_hi, "|", topic_en)

    # Hindi story (index.html)
    content_hi_raw = generate_content(topic_hi, "Hindi")
    slides_hi = parse_slides(content_hi_raw)
    img_hi = get_hd_image(topic_hi)
    canonical_hi = SITE_URL.rstrip("/") + "/"
    html_hi = build_story_html(topic_hi, slides_hi, img_hi, canonical_hi, "hi")
    save_html("index.html", html_hi)
    push_to_google(canonical_hi)

    # English story (en.html)
    content_en_raw = generate_content(topic_en, "English")
    slides_en = parse_slides(content_en_raw)
    img_en = get_hd_image(topic_en)
    en_url = SITE_URL.rstrip("/") + "/en.html"
    html_en = build_story_html(topic_en, slides_en, img_en, en_url, "en")
    save_html("en.html", html_en)
    push_to_google(en_url)

if __name__ == "__main__":
    main()
