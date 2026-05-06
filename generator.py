import os
import requests
import google.generativeai as genai

def generate_story_html(lang, topic, filename):
    try:
        # API Setup
        genai.configure(api_key=os.environ.get('GEMINI_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash') # Using latest fast model
        
        # 1. Content Generation
        prompt = f"Write a 50-word interesting story in {lang} about {topic}. Make it engaging."
        response = model.generate_content(prompt)
        story_text = response.text.replace('"', "'") # Quotes handle karne ke liye
        
        # 2. Image Fetching
        pexels_key = os.environ.get('PEXELS_KEY')
        img_url = 'https://images.pexels.com/photos/261187/pexels-photo-261187.jpeg' # Default
        
        headers = {'Authorization': pexels_key}
        r = requests.get(f'https://api.pexels.com/v1/search?query={topic}&per_page=1', headers=headers)
        
        if r.status_code == 200:
            data = r.json()
            if data.get('photos'):
                img_url = data['photos'][0]['src']['large2x']

        # 3. HTML Structure (AMP Standard)
        site_url = os.environ.get('MY_URL', 'https://example.com')
        html_content = f"""<!doctype html>
<html amp lang="{lang}">
<head>
    <meta charset="utf-8">
    <title>{topic}</title>
    <link rel="canonical" href="{site_url}/{filename}">
    <meta name="viewport" content="width=device-width,minimum-scale=1">
    <style amp-boilerplate>body{{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}}@-webkit-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-moz-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-ms-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-o-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}</style><noscript><style amp-boilerplate>body{{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}}</style></noscript>
    <script async src="https://cdn.ampproject.org/v0.js"></script>
    <script async custom-element="amp-story" src="https://cdn.ampproject.org/v0/amp-story-1.0.js"></script>
</head>
<body>
    <amp-story standalone title="{topic}" publisher="Daily Stories" publisher-logo-src="https://via.placeholder.com/96" poster-portrait-src="{img_url}">
        <amp-story-page id="p1">
            <amp-story-grid-layer template="fill">
                <amp-img src="{img_url}" width="720" height="1280" layout="responsive"></amp-img>
            </amp-story-grid-layer>
            <amp-story-grid-layer template="vertical">
                <h1 style="color:white; text-shadow: 2px 2px 4px #000;">{topic}</h1>
            </amp-story-grid-layer>
        </amp-story-page>
        <amp-story-page id="p2">
            <amp-story-grid-layer template="vertical">
                <div style="background:rgba(0,0,0,0.8); padding:20px; color:white; border-radius:10px;">
                    <p style="font-size:1.4rem; line-height:1.6;">{story_text}</p>
                </div>
            </amp-story-grid-layer>
        </amp-story-page>
    </amp-story>
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully generated {filename}")

    except Exception as e:
        print(f"Critical Error for {filename}: {e}")

if __name__ == "__main__":
    # Hindi and English stories
    generate_story_html('hi', 'आज का मुख्य समाचार', 'index.html')
    generate_story_html('en', 'Latest Trending Story', 'en.html')
