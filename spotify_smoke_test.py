
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

result = sp.search(q="Daft Punk", type="artist", limit=1)
print(result["artists"]["items"][0]["name"])
