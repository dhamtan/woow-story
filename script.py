import os
import requests
import feedparser
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from tmdbv3api import TMDb, Movie

# 1. API & Environment Setup (Zero-Error Config)
GEMINI_KEY = os.getenv("GEMINI_KEY")
PEXELS_KEY = os.getenv("PEXELS_KEY")
TMDB_KEY = os.getenv("TMDB_KEY")
SITE_URL = os.getenv("MY_URL")
JSON_FILE = 'service_account.json'

# TMDB Setup
tmdb = TMDb()
tmdb.api_key = TMDB_KEY
movie = Movie()

def get_viral_topics():
    try:
        # India Trend (Hindi)
        in_feed = feedparser.parse("https://trends.google.com")
        topic_hi = in_feed.entries[0].title if in_feed.entries else "Latest India News"
        
        # Global Movie Trend (English)
        popular_movies = movie.popular()
        topic_en = popular_movies[0].title if popular_movies else "Global Cinema Update"
        
        return topic_hi, topic_en
    except Exception as e:
        print(f"Topic Fetch Error: {e}")
        return "Top Trending India", "Global Tech News"

def generate_content(topic, lang):
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Write a 5-slide viral web story on '{topic}' in {lang}. Slide 1 must be a suspenseful hook. Max 10 words per slide. Format: Slide 1: [Text] | Slide 2: [Text]..."
        response = model.generate_content(prompt)
        return response.text if response.text else "Breaking news you must check now!"
    except:
        return "Exclusive update on this trending topic."

def get_hd_image(query):
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com{query}&per_page=1&orientation=portrait"
    try:
        res = requests.get(url, headers=headers).json()
        if 'photos' in res and len(res['photos']) > 0:
            return res['photos'][0]['src']['large2x']
    except:
        pass
    return "https://images.pexels.com"

def save_html(filename, title, content, img, canonical):
    html = f"""<!doctype html><html amp lang="en"><head><meta charset="utf-8"><title>{title}</title><link rel="canonical" href="{canonical}"><meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1"><script async src="https://cdn.ampproject.org"></script><script async custom-element="amp-story" src="https://cdn.ampproject.org"></script><style amp-boilerplate>body{{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}}@-webkit-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}</style></head><body><amp-story standalone title="{title}" publisher="AutoBot" publisher-logo-src="logo.png" poster-portrait-src="{img}"><amp-story-page id="p1"><amp-story-grid-layer template="fill"><amp-img src="{img}" width="720" height="1280" layout="responsive"></amp-img></amp-story-grid-layer><amp-story-grid-layer template="vertical"><h1>{title}</h1></amp-story-grid-layer></amp-story-page><amp-story-page id="p2"><amp-story-grid-layer template="vertical"><div style="background:rgba(0,0,0,0.7);padding:15px;color:white;">{content}</div></amp-story-grid-layer></amp-story-page></amp-story></body></html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

def push_to_google(url):
    try:
        scopes = ["https://www.googleapis.com"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scopes=scopes)
        token = creds.get_access_token().access_token
        requests.post("https://indexing.googleapis.com", 
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                      json={"url": url, "type": "URL_UPDATED"})
        print(f"Pushed to Index: {url}")
    except Exception as e:
        print(f"Indexing Error: {e}")

# MAIN EXECUTION
topic_hi, topic_en = get_viral_topics()

# Generate Hindi Story
content_hi = generate_content(topic_hi, "Hindi")
img_hi = get_hd_image(topic_hi)
save_html("index.html", topic_hi, content_hi, img_hi, SITE_URL)
push_to_google(SITE_URL)

# Generate English Story
content_en = generate_content(topic_en, "English")
img_en = get_hd_image(topic_en)
en_url = SITE_URL if SITE_URL.endswith('/') else SITE_URL + "/"
en_url += "en.html"
save_html("en.html", topic_en, content_en, img_en, en_url)
push_to_google(en_url)
