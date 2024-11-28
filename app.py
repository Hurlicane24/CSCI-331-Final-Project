import time
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

#API Credentials
CLIENT_ID = "dac33f8591f04e33a79719e5f9179df5"
CLIENT_SECRET = "1278cc26209e45dc81a507dd98f98eae"
REDIRECT_URI = "http://localhost:5000/callback"

#Globals
access_token = None
expiration_time = 0

#This function gets an access token from Spotify
def get_access_token():
    global access_token, expiration_time

    if(access_token == None or time.time() > expiration_time):
        #Prepare request
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }

        #Send request for access token and save response in the "response" variable
        response = requests.post(url, headers=headers, data=data)

        #If the response is the data we requested, parse through the data and return the access token
        if(response.status_code == 200):
            access_token = response.json().get("access_token")
            expires_in = response.json().get('expires_in', 3600)
            expiration_time = time.time() + expires_in
            return(access_token)
        
        #Else, return None
        else:
            print(f"Error: Unable to retrieve access token. STATUS: {response.status_code}")
            return(None)
        
    else:
        return(access_token)
    
#This function retrieves the top 50 playlist from Spotify
def get_top_50(access_token, endpoint):
    url = f"https://api.spotify.com/v1/{endpoint}"
    print(f"URL: {url}")
    print(f"ACCESS TOKEN: {access_token}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if(response.status_code == 200):
        return(response.json())

    else:
        print(f"Failed to fetch data. Status code {response.status_code}")
        print(f"Response: {response.text}")
        return(None)

#Route for page ("/" refers to index.html since index.html is the root of our web app)
@app.route('/')
def home():
    access_token = get_access_token()

    if(access_token):
        top_50_ID = "6WYq483WRqJRpno5suyT3Z"
        
        top_50_tracks = get_top_50(access_token, f"playlists/{top_50_ID}/tracks")

        if(top_50_tracks):
            tracks = top_50_tracks["items"]
            return(render_template("index.html", access_token=access_token, tracks=tracks))
        else:
            return(render_template("index.html", access_token=access_token, error="Could not fetch tracks"))

    else:
        return(render_template("index.html", access_token=None))

#Run the app on http://localhost:5000/
if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)