def push_index(target_url):
    try:
        scopes = ["https://www.googleapis.com"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scopes=scopes)
        token = creds.get_access_token().access_token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "url": target_url,
            "type": "URL_UPDATED"
        }
        
        response = requests.post("https://indexing.googleapis.com", headers=headers, json=data)
        print(f"Indexing Response: {response.json()}")
    except Exception as e:
        print(f"Indexing Error: {e}")

# अपनी साइट का लिंक पिंग करें
push_index(SITE_URL)
