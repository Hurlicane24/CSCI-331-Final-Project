from flask import Flask, redirect, request, render_template, session, url_for
import requests

app = Flask(__name__)
app.secret_key = 'your_random_secret_key_here'  # Ensure this is a random string

CLIENT_ID = "dac33f8591f04e33a79719e5f9179df5"
CLIENT_SECRET = "1278cc26209e45dc81a507dd98f98eae"
REDIRECT_URI = "http://localhost:5000/callback"

# Route for the homepage
@app.route('/')
def home():
    print("Home route hit.")
    if 'access_token' in session:
        print("Access token found in session.")
        access_token = session['access_token']
        
        # Check if the token is expired and refresh it if needed
        if not is_token_valid(access_token):
            access_token = refresh_access_token()
            if not access_token:
                return redirect(url_for('login'))
            session['access_token'] = access_token
        
        # Fetch the user's top tracks
        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
        headers = {"Authorization": f"Bearer {access_token}"}
        tracks_response = requests.get(top_tracks_url, headers=headers)

        if tracks_response.status_code != 200:
            return f"Failed to fetch top tracks: {tracks_response.text}"

        tracks = tracks_response.json().get('items', [])
        return render_template("index.html", tracks=tracks, access_token=access_token)
    else:
        print("No access token found, redirecting to login.")
        return redirect(url_for('login'))

# Route for Spotify login
@app.route('/login')
def login():
    print("Login route hit.")
    spotify_auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user-top-read user-read-recently-played"
    )
    return redirect(spotify_auth_url)

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    print("Session cleared. Redirecting to login.")
    return redirect(url_for('login'))

# Spotify callback route
@app.route('/callback')
def callback():
    print("Callback route hit.")
    auth_code = request.args.get('code')

    if not auth_code:
        return "Authorization failed. Please try again."

    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(token_url, data=token_data, headers=token_headers)

    if token_response.status_code != 200:
        return f"Failed to fetch access token: {token_response.text}"

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")

    # Save both the access token and refresh token in the session
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    print(f"Access token saved: {access_token}")

    # Redirect to home after successful login
    return redirect(url_for('home'))

# Route to display the recommended tracks
@app.route('/recommend.html')
def recommend():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('login'))

    # Check if the token is expired and refresh it if needed
    if not is_token_valid(access_token):
        access_token = refresh_access_token()
        if not access_token:
            return redirect(url_for('login'))
        session['access_token'] = access_token

    # Fetch the user's most recent 20 tracks
    recent_tracks_url = "https://api.spotify.com/v1/me/player/recently-played?limit=20"
    headers = {"Authorization": f"Bearer {access_token}"}
    tracks_response = requests.get(recent_tracks_url, headers=headers)

    if tracks_response.status_code != 200:
        return f"Failed to fetch recently played tracks: {tracks_response.text}"

    tracks = tracks_response.json().get('items', [])
    
    return render_template("recommend.html", tracks=tracks)

# Function to check if the access token is still valid
def is_token_valid(access_token):
    test_url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(test_url, headers=headers)
    
    # If the response code is 401, the token is invalid
    return response.status_code != 401

# Function to refresh the access token using the refresh token
def refresh_access_token():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return None

    refresh_url = "https://accounts.spotify.com/api/token"
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    refresh_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    refresh_response = requests.post(refresh_url, data=refresh_data, headers=refresh_headers)

    if refresh_response.status_code != 200:
        return None

    new_token_data = refresh_response.json()
    session['access_token'] = new_token_data.get("access_token")
    return session['access_token']

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)