"""
spotify_service.py — Spotify API integration layer.

Strategy: Artist Search + Top Tracks (Free-account compatible)
══════════════════════════════════════════════════════════════════
WHY playlists were dropped
──────────────────────────
Fetching tracks from Spotify-owned playlists (e.g. "Today's Top Hits")
via GET /playlists/{id}/tracks requires the *playlist owner's* account to
have an active Premium subscription when accessed through a third-party app.
Free developer accounts therefore receive:

    403 Forbidden — "Player command failed: Premium required"

WHY artist search works on free accounts
─────────────────────────────────────────
The following endpoints are available under Client Credentials flow with
NO Premium requirement:

    GET /search?type=artist          → resolve artist name → artist ID
    GET /artists/{id}/top-tracks     → top 10 tracks incl. preview_url

Both endpoints return `preview_url` (a 30-second MP3 hosted by Spotify CDN)
without any playback permission checks.  Downloading that URL requires only
a plain HTTP GET — no OAuth scope, no Premium.

Public API reference:
  https://developer.spotify.com/documentation/web-api/reference/get-an-artists-top-tracks
"""

import random
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


# ── Data transfer object ───────────────────────────────────────────────────

@dataclass
class TrackInfo:
    """Immutable snapshot of one Spotify track."""
    track_id:    str
    title:       str
    artist:      str
    album:       str
    preview_url: Optional[str]   # 30-second MP3 URL; None when unavailable
    source:      str             # artist name used to find this track

    @property
    def has_preview(self) -> bool:
        return bool(self.preview_url)

    def __str__(self) -> str:
        return f'"{self.title}" by {self.artist}'


# ── Exceptions ─────────────────────────────────────────────────────────────

class SpotifyAuthError(Exception):
    """Raised when the Client Credentials token cannot be obtained."""


class SpotifyFetchError(Exception):
    """Raised when any Spotify API call fails or returns no usable data."""


# ── Service ────────────────────────────────────────────────────────────────

# Default artist pool — broad genre mix to maximise preview availability.
# All are globally recognised acts with well-populated top-track lists.
DEFAULT_ARTISTS: List[str] = [
    "Daft Punk",
    "Coldplay",
    "Adele",
    "The Weeknd",
    "Imagine Dragons",
    "Ed Sheeran",
    "Billie Eilish",
    "Ariana Grande",
    "Drake",
    "Taylor Swift",
    "Post Malone",
    "Eminem",
    "Rihanna",
    "Beyoncé",
    "Bruno Mars",
    "Lady Gaga",
    "Kendrick Lamar",
    "Justin Bieber",
    "Dua Lipa",
    "The Chainsmokers",
    "Linkin Park",
    "Green Day",
    "Radiohead",
    "Tame Impala",
    "Arctic Monkeys",
    "Fleetwood Mac",
    "Queen",
    "David Bowie",
    "Michael Jackson",
    "Elvis Presley",
]


class SpotifyService:
    """
    Spotify Web API client using the Client Credentials flow.

    No user login, no redirect URI, no Premium required.

    Typical usage
    ─────────────
        svc = SpotifyService(client_id, client_secret)
        tracks = svc.fetch_rounds(artist_names, count=5)
        for track in tracks:
            print(track)          # "Song Title" by Artist Name
            print(track.preview_url)
    """

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE  = "https://api.spotify.com/v1"

    def __init__(self, client_id: str, client_secret: str) -> None:
        if not client_id or not client_secret:
            raise SpotifyAuthError(
                "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set. "
                "Get them at https://developer.spotify.com/dashboard"
            )
        self._client_id     = client_id
        self._client_secret = client_secret
        self._access_token: Optional[str] = None

        # Cache artist name → Spotify artist ID to avoid redundant searches
        self._artist_id_cache: Dict[str, str] = {}

    # ── Authentication ─────────────────────────────────────────────────────

    def _get_token(self) -> str:
        """
        Request a fresh Client Credentials OAuth token.
        This flow requires only client_id + client_secret — no user login.
        """
        resp = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(self._client_id, self._client_secret),
            timeout=10,
        )
        if resp.status_code != 200:
            raise SpotifyAuthError(
                f"Token request failed ({resp.status_code}): {resp.text[:300]}"
            )
        token = resp.json().get("access_token")
        if not token:
            raise SpotifyAuthError("Spotify returned no access_token.")
        logger.debug("Obtained new access token.")
        return token

    def _headers(self) -> dict:
        """Return Bearer auth headers, lazily fetching a token if needed."""
        if not self._access_token:
            self._access_token = self._get_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """
        Authenticated GET with automatic token refresh on 401.
        Raises SpotifyFetchError for any non-200 response.
        """
        for attempt in range(2):
            resp = requests.get(
                url, headers=self._headers(), params=params, timeout=10
            )
            if resp.status_code == 401 and attempt == 0:
                logger.debug("Token expired — refreshing.")
                self._access_token = self._get_token()
                continue
            if resp.status_code != 200:
                raise SpotifyFetchError(
                    f"Spotify API {resp.status_code} for {url}: "
                    f"{resp.text[:200]}"
                )
            return resp.json()
        raise SpotifyFetchError("Exhausted token refresh retries.")

    # ── Artist resolution ──────────────────────────────────────────────────

    def _resolve_artist_id(self, artist_name: str) -> Optional[str]:
        """
        Search for `artist_name` and return its Spotify artist ID.

        Uses GET /search?type=artist — available on free accounts.
        Results are cached for the lifetime of this service instance.

        Returns None if no matching artist is found (graceful degradation).
        """
        if artist_name in self._artist_id_cache:
            return self._artist_id_cache[artist_name]

        try:
            data = self._get(
                f"{self.API_BASE}/search",
                params={"q": artist_name, "type": "artist", "limit": 1},
            )
        except SpotifyFetchError as exc:
            logger.warning("Artist search failed for '%s': %s", artist_name, exc)
            return None

        items = data.get("artists", {}).get("items", [])
        if not items:
            logger.warning("No artist found for query '%s'.", artist_name)
            return None

        artist_id = items[0]["id"]
        logger.debug("Resolved '%s' → artist ID %s", artist_name, artist_id)
        self._artist_id_cache[artist_name] = artist_id
        return artist_id

    # ── Top-track fetching ─────────────────────────────────────────────────

    def get_artist_top_tracks(self, artist_name: str) -> List[TrackInfo]:
        """
        Return the artist's top tracks (up to 10) that have a preview URL.

        Endpoint: GET /artists/{id}/top-tracks
        ─────────────────────────────────────
        • No Premium required.
        • Returns at most 10 tracks ranked by Spotify popularity.
        • `preview_url` is present on most (but not all) tracks.
          Tracks without it are filtered out before returning.

        Args:
            artist_name: Human-readable artist name (e.g. "Coldplay").

        Returns:
            List of TrackInfo with preview_url guaranteed non-None.
            Empty list if the artist cannot be resolved or has no previews.
        """
        artist_id = self._resolve_artist_id(artist_name)
        if not artist_id:
            return []

        try:
            # `market` parameter is required by this endpoint.
            # "US" is the most broadly available market for previews.
            data = self._get(
                f"{self.API_BASE}/artists/{artist_id}/top-tracks",
                params={"market": "US"},
            )
        except SpotifyFetchError as exc:
            logger.warning(
                "Could not fetch top tracks for '%s': %s", artist_name, exc
            )
            return []

        tracks: List[TrackInfo] = []
        for raw in data.get("tracks", []):
            preview_url = raw.get("preview_url")
            if not preview_url:
                # Spotify omits preview_url for some tracks — skip them.
                logger.debug(
                    "Track '%s' has no preview_url — skipped.", raw.get("name")
                )
                continue

            artists  = raw.get("artists", [])
            artist_n = artists[0]["name"] if artists else artist_name
            album    = raw.get("album", {}).get("name", "")

            tracks.append(TrackInfo(
                track_id    = raw["id"],
                title       = raw["name"],
                artist      = artist_n,
                album       = album,
                preview_url = preview_url,
                source      = artist_name,
            ))

        logger.debug(
            "Artist '%s': %d previewable top tracks found.", artist_name, len(tracks)
        )
        return tracks

    # ── Random track selection ─────────────────────────────────────────────

    def get_random_track_by_artist(
        self, artist_names: List[str], exclude_ids: Optional[set] = None
    ) -> Optional[TrackInfo]:
        """
        Pick one random previewable track from a randomly chosen artist.

        Strategy:
          1. Shuffle the artist list so every call gets a different ordering.
          2. For each artist, fetch their top tracks with preview URLs.
          3. From the remaining (non-excluded) tracks, pick one at random.
          4. If an artist yields nothing, move to the next — no hard failure.

        Args:
            artist_names:  Pool of artist names to draw from.
            exclude_ids:   Set of track_ids already used this session.

        Returns:
            A TrackInfo, or None if the entire pool is exhausted.
        """
        exclude_ids = exclude_ids or set()
        shuffled = random.sample(artist_names, len(artist_names))

        for artist_name in shuffled:
            tracks = self.get_artist_top_tracks(artist_name)
            available = [t for t in tracks if t.track_id not in exclude_ids]
            if available:
                chosen = random.choice(available)
                logger.info("Selected: %s", chosen)
                return chosen
            logger.debug(
                "Artist '%s' had no unused previewable tracks.", artist_name
            )

        logger.warning("Entire artist pool exhausted — no track found.")
        return None

    # ── Batch pre-fetch ────────────────────────────────────────────────────

    def fetch_rounds(
        self, artist_names: List[str], count: int
    ) -> List[TrackInfo]:
        """
        Pre-fetch `count` unique, previewable tracks before the game starts.

        Called once by GameEngine so there are no mid-game API pauses.
        Signature intentionally mirrors the old playlist-based version so
        GameEngine requires only a one-line config key change.

        Args:
            artist_names: Pool of artist names (from GameConfig).
            count:        Number of rounds / tracks needed.

        Raises:
            SpotifyFetchError: If fewer than `count` tracks can be found.
        """
        if not artist_names:
            raise SpotifyFetchError(
                "No artists configured. Add names to GameConfig.spotify_artists."
            )

        tracks:   List[TrackInfo] = []
        used_ids: set             = set()

        for attempt in range(count * 5):   # generous headroom for sparse previews
            if len(tracks) >= count:
                break

            track = self.get_random_track_by_artist(artist_names, exclude_ids=used_ids)
            if track is None:
                # All artists checked — pool is exhausted
                break

            # Deduplicate (get_random_track_by_artist already respects used_ids,
            # but this guard covers any edge-case race)
            if track.track_id not in used_ids:
                tracks.append(track)
                used_ids.add(track.track_id)
                logger.debug(
                    "Pre-fetched %d/%d: %s", len(tracks), count, track
                )

        if len(tracks) < count:
            raise SpotifyFetchError(
                f"Only found {len(tracks)} previewable tracks, needed {count}. "
                "Try adding more artists to GameConfig.spotify_artists, or "
                "check that your SPOTIPY_CLIENT_ID / SPOTIPY_CLIENT_SECRET are correct."
            )

        return tracks
