from flask import Flask, render_template, request 
import requests, json, datetime, base64, random, os
from dotenv import load_dotenv

app = Flask('MusicSuggestionTool') 

load_dotenv()

def get_headers(): 
  client_id = os.getenv("CLIENT_ID")
  client_secret = os.getenv("CLIENT_SECRET")

  auth_str = f"{client_id}:{client_secret}"
  base64_auth_str = base64.b64encode(auth_str.encode()).decode()

  headers = {
    'Authorization': f'Basic {base64_auth_str}',
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  data = {
    'grant_type': 'client_credentials'
  }

  response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

  if response.status_code == 200:
      token_info = response.json()
      access_token = token_info['access_token']

      headers = {
        'Authorization': f'Bearer {access_token}', 
        'Accept': 'application/json', 
        'Content-Type': 'application/json'
      }
      return headers
  
  else:
      print(f"Failed to get access token. Status code: {response.status_code}")
  return ""


def get_coverimage(playlist_id):
  headers = get_headers()

  endpoint="https://api.spotify.com/v1/playlists/" + playlist_id + "/images"

  response = requests.get(endpoint, headers=headers)
  if response.status_code != 200:
      raise Exception("Failed to retrieve the cover image of the playlist.")
  
  response_json = response.json()
  return (response_json[0]['url'])


def get_playlistdetails(playlist_id): 
  endpoint=f"https://api.spotify.com/v1/playlists/{playlist_id}?fields=name%2Cowner%2Ctracks%28total%2C+items%28added_at%2C+track%28album%28release_date%2C+id%29%2C+artists%28id%29%2C+duration_ms%29%29%29"

  headers = get_headers()

  response = requests.get(endpoint, headers=headers)

  if response.status_code != 200:
    raise Exception("Failed to retrieve the playlist information")
    
  response_json = response.json()
  playlist_name = response_json['name']
  owner = response_json['owner']['display_name']
  track_count = response_json['tracks']['total']

  tracks = response_json['tracks']['items']

  decade_list = []
  playlist_updated = []
  track_durations = []
  artists = []
  album_ids = []

  for track in tracks:
    if track['track']:
      playlist_updated.append(track['added_at']) 
      track_durations.append(track['track']['duration_ms'])
      artists.append(track['track']['artists'])
      album_ids.append(track['track']['album']['id'])

      try:
        release_date = datetime.datetime.strptime(track['track']['album']['release_date'], '%Y-%m-%d') 
        year = release_date.year
      except ValueError:
        year = int(track['track']['album']['release_date'][:4])
      finally:
        decade = (year // 10) * 10
        decade_list.append(decade)

  artist_ids = [artist['id'] for sublist in artists for artist in sublist]

  decade_count = {}
  for decade in decade_list: 
    if decade in decade_count:
        decade_count[decade] += 1
    else:
        decade_count[decade] = 1
      
  common_decade = max(decade_count, key=decade_count.get) 
  common_decade = str(common_decade) + 's' 
 
  dates = [datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ') for date in playlist_updated]
  sorted_dates = sorted(dates, reverse=True)
  last_edit = sorted_dates[0].strftime('%Y-%m-%dT%H:%M:%SZ')  
  date_obj = datetime.datetime.strptime(last_edit, "%Y-%m-%dT%H:%M:%SZ") 
  last_edit = date_obj.strftime("%B %Y")

  duration_total = 0 
  for duration in track_durations: 
    duration_total += duration

  average_duration = duration_total // len(tracks)
  minute = average_duration // 60000 
  second = round((average_duration % 60000) / 1000)
  average_duration = str(minute) + ":" + str(second)

  return playlist_name, owner, track_count, average_duration, artist_ids, common_decade, last_edit, album_ids


def get_genres(artist_ids):
  artist_ids = "%2C".join(artist_ids)

  endpoint = f"https://api.spotify.com/v1/artists?ids={artist_ids}"
  
  headers = get_headers()
  response = requests.get(endpoint, headers=headers)

  if response.status_code != 200:
    raise Exception("Failed to retrieve the top genre of the playlist")
  
  response_json = response.json()
  
  genres = [artist['genres'] for artist in response_json['artists']]
  return genres


def get_topgenre(genres): 
  genre_count = {}
  for genre_list in genres:
    for genre in genre_list:
      if genre in genre_count:
        genre_count[genre] += 1
      else:
          genre_count[genre] = 1

  top_genre = max(genre_count, key=genre_count.get) 
  return top_genre


def get_recommendations(album_ids, count):
  albums = ','.join(album_ids)
  endpoint = f"https://api.spotify.com/v1/albums?ids={albums}"

  headers = get_headers()

  response = requests.get(endpoint, headers=headers)
    
  if response.status_code != 200:
    raise Exception("Failed to retrieve album details")
  
  response_json = response.json()

  album_details = response_json["albums"]
  albums = [album['tracks']['items'] for album in album_details]
  track_ids = [track['id'] for album in albums for track in album]

  recommendation_list = []
  for i in range(count):
    selection = random.randint(0, len(track_ids) - 1)
    recommendation_list.append(track_ids[selection])
  return recommendation_list


def get_trackdetails(track_list):
  tracks = ",".join(track_list)
  endpoint = f"https://api.spotify.com/v1/tracks?ids={tracks}"

  headers = get_headers()

  response = requests.get(endpoint, headers=headers)
    
  if response.status_code != 200:
    raise Exception("Failed to retrieve track information")
  
  response_json = response.json()

  tracks = response_json['tracks']

  track_details = []
  total_duration = 0
  for track in tracks: 
    temp = []
    temp.append(track["name"])
    temp.append(track["album"]["images"][0]["url"])

    artist_names = [artist['name'] for artist in track['artists']]
    temp.append(artist_names)

    temp.append(track["id"])
    release_date = track["album"]["release_date"]

    if (len(release_date) == 10):
      release_date = datetime.datetime.strptime(release_date, '%Y-%m-%d').strftime('%d/%m/%Y')
    elif (len(release_date) == 7):
      release_date = datetime.datetime.strptime(release_date, '%Y-%m').strftime('%m/%Y')
    elif (len(release_date) == 4):
      release_date = datetime.datetime.strptime(release_date, '%Y')
    else: 
      release_date = ""

    temp.append(release_date)

    total_duration += track["duration_ms"]

    track_details.append(temp)

  minute = total_duration // 60000
  second = round((total_duration % 60000) / 1000)
  total_duration = str(minute) + " minutes, " + str(second) + " seconds" 

  return track_details, total_duration


def get_genrerecommend():  
  genreselect = str(request.cookies.get('genre'))
  endpoint = f"https://api.spotify.com/v1/search?q=genre:{genreselect}&limit=20&type=track"
  
  headers = get_headers()
  response = requests.get(endpoint,headers=headers)
  
  if response.status_code != 200:
    raise Exception("Failed to retrieve recommendations based on genre")

  response_json = response.json()

  tracks = response_json["tracks"]["items"]
  track_details = []
  total_duration = 0
  banned_words = ["Christmas", "Xmas", "Sleigh", "Snow", "Santa", "Frosty", "Winter", "Rudolph", "Underneath", "Deck", "MacColl"]

  for track in tracks: 
    if not(any(word in track["name"] for word in banned_words)):
      temp = []
      temp.append(track["name"])
      temp.append(track["album"]["images"][0]["url"])

      artist_names = [artist['name'] for artist in track['artists']]
      temp.append(artist_names)

      temp.append(track["id"])
      release_date = track["album"]["release_date"]

      if (len(release_date) == 10):
        release_date = datetime.datetime.strptime(release_date, '%Y-%m-%d').strftime('%d/%m/%Y')
      elif (len(release_date) == 7):
        release_date = datetime.datetime.strptime(release_date, '%Y-%m').strftime('%m/%Y')
      elif (len(release_date) == 4):
        release_date = datetime.datetime.strptime(release_date, '%Y')
      else: 
        release_date = ""

      temp.append(release_date)

      total_duration += track["duration_ms"]

      track_details.append(temp)

  minute = total_duration // 60000
  second = round((total_duration % 60000) / 1000)
  total_duration = str(minute) + " minutes, " + str(second) + " seconds" 

  return track_details, total_duration


#APP ROUTES 
@app.route('/')  
def home_page(): 
  return render_template('index.html')

@app.route('/genre') 
def genre_page():
  return render_template('genre.html')

@app.route('/playlist', methods=['GET','POST']) 
def playlist_page():
  if request.method == 'POST':
    request.get_json(force=True,silent=True)
    return {'message': 'ok'} 
  else:
    return render_template('playlist.html')

@app.route('/genreresults') 
def genreresults_page():
  recommended_songs, total_duration = get_genrerecommend()
  return render_template('genreresults.html', genre_recommendations=recommended_songs, genrelength=total_duration, song_count=len(recommended_songs)) 

@app.route('/playlistresults/<playlist_id>') 
def playlistresults_page(playlist_id):
  image_url = get_coverimage(playlist_id)
  playlist_name, playlist_owner, track_total, average_duration, artist_ids, common_decade, last_edit, album_ids = get_playlistdetails(playlist_id)

  if (track_total < 5): 
    raise Exception('The playlist is too short. Please try adding some songs to the playlist.')

  elif (track_total > 50):
    artist_ids = artist_ids[:50]
    album_ids = album_ids[:50]
 
  genres = get_genres(artist_ids)
  top_genre = get_topgenre(genres)

  if (len(album_ids) <= 20):
    recommendations = get_recommendations(album_ids, 10)
  elif (len(album_ids) <= 40): 
    recommendations = get_recommendations(album_ids[0:20], 5) + get_recommendations(album_ids[20:], 5)
  else: 
    recommendations = get_recommendations(album_ids[0:20], 3) + get_recommendations(album_ids[20:40], 4) + get_recommendations(album_ids[40:], 3)

  track_details, recommend_duration = get_trackdetails(recommendations)

  return render_template('playlistresults.html', image_url=image_url, playlist_name=playlist_name, playlist_owner=playlist_owner, track_total=track_total, duration=average_duration, top_genre=top_genre, common_decade=common_decade, last_edit=last_edit, recommend_info=track_details, song_count=len(recommendations), recommend_length=recommend_duration) 

app.run(host='0.0.0.0')