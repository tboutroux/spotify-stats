from flask import Flask, redirect, request, url_for, session, render_template
import requests
import base64
import json
import os
from collections import Counter
import urllib.parse
from db import create_line, read_lines, update_line, delete_line, line_exists, get_db_connection

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

def get_genre_id(genre_name):
    """
    Retrieve the ID of a genre based on its name.

    Args:
        genre_name (str): The name of the genre.

    Returns:
        int: The ID of the genre, or None if not found.
    """
    cnx = get_db_connection()
    if cnx is None:
        return None

    query = "SELECT id FROM genre WHERE name = %s"

    try:
        cursor = cnx.cursor()
        cursor.execute(query, (genre_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as err:
        print(f"Error: {err}")

def get_album_details(access_token, album_id):
    """
    Retrieve album details from Spotify API.

    Args:
        access_token (str): The access token for Spotify API.
        album_id (str): The Spotify album ID.

    Returns:
        dict: The album details if successful, None otherwise.
    """
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://api.spotify.com/v1/albums/{album_id}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching album details: {response.status_code} - {response.json()}")
        return None


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

    # Insérer les artistes dans la base de données
    for artist in artists:
        artist_data = {
            'id': artist['id'],
            'name': artist['name'],
            'popularity': artist['popularity'],
            'photo': artist['images'][0]['url'] if artist['images'] else ''
        }
        if not line_exists('artiste', {'id': artist['id']}):
            create_line('artiste', artist_data)

    # Insérer les genres dans la base de données
    for artist in artists:
        for genre in artist['genres']:
            if not line_exists('genre', {'name': genre}):
                genre_data = {'name': genre}
                create_line('genre', genre_data)
            
            genre_id = get_genre_id(genre)  # Fonction pour récupérer l'id du genre
            artiste_genre_data = {
                'artiste_id': artist['id'],
                'genre_id': genre_id
            }
            if not line_exists('artiste_genre', artiste_genre_data):
                create_line('artiste_genre', artiste_genre_data)

    # Insérer les albums et tracks dans la base de données
    for track in tracks:
        album_id = track['track']['album']['id']
        album_details = get_album_details(access_token, album_id)
        if album_details:
            album_data = {
                'id': album_details['id'],
                'name': album_details['name'],
                'release_date': album_details['release_date'],
                'total_tracks': album_details['total_tracks'],
                'popularity': album_details.get('popularity', 0),
                'photo': album_details['images'][0]['url'] if album_details['images'] else ''
            }
            if not line_exists('album', {'id': album_data['id']}):
                create_line('album', album_data)

            track_data = {
                'id': track['track']['id'],
                'name': track['track']['name'],
                'duration_ms': track['track']['duration_ms'],
                'popularity': track['track']['popularity'],
                'release_date': album_details['release_date'],
                'photo': album_details['images'][0]['url'] if album_details['images'] else ''
            }
            if not line_exists('track', {'id': track_data['id']}):
                create_line('track', track_data)

            # Insérer les relations artiste-track et album-track
            for artist in track['track']['artists']:
                artiste_track_data = {
                    'artiste_id': artist['id'],
                    'track_id': track['track']['id']
                }
                if not line_exists('artiste_track', artiste_track_data):
                    create_line('artiste_track', artiste_track_data)

            album_track_data = {
                'album_id': album_id,
                'track_id': track['track']['id']
            }
            if not line_exists('album_track', album_track_data):
                create_line('album_track', album_track_data)

            # Insérer les relations artiste-album
            for artist in track['track']['artists']:
                artiste_album_data = {
                    'artiste_id': artist['id'],
                    'album_id': album_id
                }
                if not line_exists('artiste_album', artiste_album_data):
                    create_line('artiste_album', artiste_album_data)

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

@app.route('/database')
def database():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('index'))

    # Connexion à la base de données
    cnx = get_db_connection()
    if cnx is None:
        return "Erreur de connexion à la base de données."

    try:
        cursor = cnx.cursor(dictionary=True)

        # Récupération des données des artistes
        cursor.execute("SELECT * FROM artiste")
        artistes = cursor.fetchall()

        # Récupération des données des albums
        cursor.execute("SELECT * FROM album")
        albums = cursor.fetchall()

        # Récupération des données des pistes
        cursor.execute("SELECT * FROM track")
        tracks = cursor.fetchall()

        # Récupération des données des genres
        cursor.execute("SELECT * FROM genre")
        genres = cursor.fetchall()

        # Récupération des relations artistes-albums
        cursor.execute("SELECT * FROM artiste_album")
        artiste_album_relations = cursor.fetchall()

        # Récupération des relations artistes-pistes
        cursor.execute("SELECT * FROM artiste_track")
        artiste_track_relations = cursor.fetchall()

        # Récupération des relations albums-pistes
        cursor.execute("SELECT * FROM album_track")
        album_track_relations = cursor.fetchall()

        # Récupération des relations artistes-genres
        cursor.execute("SELECT * FROM artiste_genre")
        artiste_genre_relations = cursor.fetchall()

    except mysql.connector.Error as err:
        return f"Erreur de la base de données : {err}"
    finally:
        cursor.close()
        cnx.close()

    return render_template('database.html',
                           artistes=artistes,
                           albums=albums,
                           tracks=tracks,
                           genres=genres,
                           artiste_album_relations=artiste_album_relations,
                           artiste_track_relations=artiste_track_relations,
                           album_track_relations=album_track_relations,
                           artiste_genre_relations=artiste_genre_relations)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
