from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
import os
import requests
import base64
import urllib.parse

load_dotenv()  # Load environment variables from .env

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

app = Flask(__name__)

# Mood dictionary
mood_dict = {
    "happy": "happy",
    "sad": "sad",
    "bad": "upset/sad",
    "upset": "angry/sad",
    "excited": "excited",
    "tired": "tired",
    "bored": "bored",
    "lonely": "lonely",
    "anxious": "anxious",
    "stressed": "stressed",
    "angry": "angry",
    "not good": "sad",
    "feeling down": "sad",
    "very happy": "happy",
    "shit": "unhappy/sad",
    "good": "good",
    "silly": "silly",
    "goofy": "silly",
    "in love": "love",
    "love": "love"
}

# Map detected moods to Spotify search queries
mood_to_query = {
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "excited": "party",
    "tired": "chill",
    "bored": "focus",
    "lonely": "melancholy",
    "anxious": "calm",
    "stressed": "relax",
    "neutral": "chill",
    "silly": "silly",
    "love": "love"
}

# Step 1: Show form
@app.route('/')
def song():
    return render_template("index.html")

# Step 2: Detect mood
@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['song_prompt']
    print("User typed:", user_input)

    detected_moods = []

    # Multi-word phrases first
    for phrase in mood_dict:
        if " " in phrase and phrase in user_input.lower():
            detected_moods.append(mood_dict[phrase])

    # Single words
    if not detected_moods:
        for word in user_input.lower().split():
            if word in mood_dict:
                detected_moods.append(mood_dict[word])

    # Default to neutral if nothing matched
    if not detected_moods:
        detected_moods.append("neutral")

    print("Detected moods:", detected_moods)

    # Pass mood to Spotify login
    mood_param = urllib.parse.quote(detected_moods[0])
    return redirect(f"/login?mood={mood_param}")

# Step 3: Start Spotify auth
@app.route("/login")
def login():
    mood = request.args.get("mood")
    scopes = "user-read-private"
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(SPOTIFY_REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(scopes)}"
        f"&state={mood}"
    )
    return redirect(auth_url)

# Step 4: Handle Spotify callback and show tracks
@app.route("/callback")
def callback():
    auth_code = request.args.get("code")
    mood = request.args.get("state")  # Retrieved mood from state

    # Request access token
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    r = requests.post(token_url, data=data, headers=headers)
    r_data = r.json()
    access_token = r_data.get("access_token")

    # Fetch tracks from Spotify
    tracks = []
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"q": mood_to_query.get(mood, "chill"), "type": "track", "limit": 5}
        search_resp = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
        items = search_resp.json().get("tracks", {}).get("items", [])
        for item in items:
            tracks.append({
                "name": item['name'],
                "artist": item['artists'][0]['name'],
                "preview_url": item['preview_url'],  # 30s preview
                "spotify_url": item['external_urls']['spotify']
            })

    return render_template("results.html", mood=mood, tracks=tracks)

if __name__ == "__main__":
    app.run(debug=True)
