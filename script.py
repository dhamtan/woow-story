import os, requests, feedparser
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from tmdbv3api import TMDb, Movie

# 1. Configuration & API Loading
GEMINI_KEY = os.getenv("GEMINI_KEY")
PEXELS_KEY = os.getenv("PEXELS_KEY")
TMDB_KEY = os.getenv("TMDB_KEY")
SITE_URL = os.getenv("MY_URL")
JSON_FILE = 'service_account.json'

# 2. Topic Discovery (High Demand Source)
# हम US (High CPM) और India (High Volume) दोनों के ट्रेंड्स ले रहे हैं
tmdb = TMDb()
tmdb.api_key = TMDB_KEY
movie_data = Movie().popular()
movie_topic = movie_data[0].title if movie_data else "Next Big Tech Revolution"

in_trends = feedparser.parse("https://trends.google.com")
india_topic = in_trends.entries[0].title if in_trends.entries else "Breaking Tech News"

# 3. AI Content Generation (Zero-Error Prompting)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def generate_viral_content(topic, lang):
    # Pro Prompt: सस्पेंस और हाई सीटीआर (CTR) के लिए
    prompt = f"Write a 5-slide viral web story on '{topic}' in {lang}. Use a suspenseful hook in Slide 1. Keep each slide under 12 words. Focus on 'Why this matters now'. Format: Slide 1: [Title] | Slide 2: [Text]..."
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "Information you need to see now!"
    except:
        return "Breaking updates on this trending topic."

story_hi = generate_viral_content(india_topic, "Hindi")
story_en = generate_viral_content(movie_topic, "English")

# 4. HD Image Engine (Automatic Fallback)
def get_hd_img(query):
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(f"https://api.pexels.com{query}&per_page=1&orientation=portrait", headers=headers).json()
        if res.get('photos'): return res['photos'][0]['src']['large2x']
    except: pass
    return "https://images.pexels.com" # Default High Quality Backup

img_hi = get_hd_img(india_topic)
img_en = get_hd_img(movie_topic)

# 5. Zero-Error HTML Generator (AMP Standard)
def build_html(filename, title, content, img, canonical):
    html = f"""<!doctype html><html amp lang="en"><head><meta charset="utf-8"><title>{title}</title><link rel="canonical" href="{canonical}"><meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1"><script async src="https://cdn.ampproject.org"></script><script async custom-element="amp-story" src="https://cdn.ampproject.org"></script><style amp-boilerplate>body{{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}}@-webkit-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}</style></head><body><amp-story standalone title="{title}" publisher="AutoTrends" publisher-logo-src="logo.png" poster-portrait-src="{img}"><amp-story-page id="p1"><amp-story-grid-layer template="fill"><amp-img src="{img}" width="720" height="1280" layout="responsive"></amp-img></amp-story-grid-layer><amp-story-grid-layer template="vertical"><h1>{title}</h1></amp-story-grid-layer></amp-story-page><amp-story-page id="p2"><amp-story-grid-layer template="vertical"><div style="background:rgba(0,0,0,0.7);padding:15px;color:white;font-size:1.2em;">{content}</div></amp-story-grid-layer></amp-story-page></amp-story></body></html>"""
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

build_html("index.html", india_topic, story_hi, img_hi, SITE_URL)
build_html("en.html", movie_topic, story_en, img_en, f"{SITE_URL}en.html")

# 6. Instant Google Indexing (Dual Sync)
def push_to_google(url):
    try:
        scopes = ["https://www.googleapis.com"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scopes=scopes)
        token = creds.get_access_token().access_token
        requests.post("https://indexing.googleapis.com", 
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                      json={"url": url, "type": "URL_UPDATED"})
        print(f"Pushed: {url}")
    except Exception as e: print(f"Index Error: {e}")

push_to_google(SITE_URL)
push_index_url = f"{SITE_URL}en.html" if SITE_URL.endswith('/') else f"{SITE_URL}/en.html"
push_to_google(push_index_url)
