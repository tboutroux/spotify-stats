from flask import Flask, redirect, request, url_for, session, render_template
import requests
import base64
import json
import os
from collections import Counter
import urllib.parse

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Changez cette clé pour quelque chose de sécurisé

# Charger les configurations depuis config.json
with open(os.path.join('conf', 'config.json')) as config_file:
    config = json.load(config_file)

client_id = config['spotify']['client_id']
client_secret = config['spotify']['client_secret']
redirect_uri = config['spotify']['redirect_uri']
scope = 'user-read-recently-played user-top-read user-library-read'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    auth_url = 'https://accounts.spotify.com/authorize'
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope
    }
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = "https://accounts.spotify.com/api/token"
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    token_headers = {
        "Authorization": f"Basic {client_creds_b64}"
    }

    r = requests.post(token_url, data=token_data, headers=token_headers)
    token_response_data = r.json()
    session['access_token'] = token_response_data["access_token"]

    return redirect(url_for('stats'))


def get_all_recently_played_tracks(access_token):
    recently_played_url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    limit = 50  # Nombre maximum de chansons par requête
    before = None
    all_tracks = []
    offset = 0

    while True:
        params = {
            "limit": limit,
            "offset": offset
        }
        if before:
            params["before"] = before
            offset += limit

        response = requests.get(recently_played_url, headers=headers, params=params)
        if response.status_code != 200:
            return None, f"Erreur {response.status_code}: {response.text}"

        recently_played = response.json()
        if not recently_played['items']:
            break

        all_tracks.extend(recently_played['items'])
        before = recently_played['cursors']['before'] if 'cursors' in recently_played else None
        if not before:
            break

    return all_tracks, None


def get_artist_genres(access_token, artist_ids):
    artist_url = "https://api.spotify.com/v1/artists"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "ids": ",".join(artist_ids)
    }

    response = requests.get(artist_url, headers=headers, params=params)
    if response.status_code != 200:
        return None, f"Erreur {response.status_code}: {response.text}"

    artists = response.json()['artists']
    return artists, None


@app.route('/stats')
def stats():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('index'))

    tracks, error = get_all_recently_played_tracks(access_token)
    if error:
        return error

    # Récupérer les artistes uniques
    artist_ids = list(set(item['track']['artists'][0]['id'] for item in tracks))
    artists, error = get_artist_genres(access_token, artist_ids)
    if error:
        return error

    # Statistiques
    total_tracks = len(tracks)
    total_minutes = sum(item['track']['duration_ms'] for item in tracks) / 60000  # Convertir ms en minutes
    artist_counter = Counter([item['track']['artists'][0]['name'] for item in tracks])
    top_artists = artist_counter.most_common(10)
    genre_counter = Counter()
    for artist in artists:
        for genre in artist['genres']:
            genre_counter[genre] += 1
    top_genres = genre_counter.most_common(10)

    track_details = [{
        'name': item['track']['name'],
        'artist': item['track']['artists'][0]['name'],
        'album': item['track']['album']['name'],
        'played_at': item['played_at'],
        'image_url': item['track']['album']['images'][0]['url']
    } for item in tracks]

    return render_template('stats.html', 
                           total_tracks=total_tracks, 
                           total_minutes=total_minutes,
                           top_artists=top_artists,
                           top_genres=top_genres,
                           track_details=track_details)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
