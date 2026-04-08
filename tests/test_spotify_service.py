"""
tests/test_spotify_service.py — Unit tests for SpotifyService (artist strategy).

All Spotify HTTP calls are mocked — no real credentials needed.
Run with:  python -m pytest tests/ -v
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spotify_service import SpotifyService, TrackInfo, SpotifyAuthError, SpotifyFetchError


# ── Helpers ────────────────────────────────────────────────────────────────

def _mock_response(status_code: int, body: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = json.dumps(body)
    return resp


def _token_response() -> MagicMock:
    return _mock_response(200, {"access_token": "test_token_abc"})


def _artist_search_response(artist_id: str = "artist123") -> MagicMock:
    return _mock_response(200, {
        "artists": {
            "items": [{"id": artist_id, "name": "Coldplay"}]
        }
    })


def _top_tracks_response(with_previews: int = 3, without_previews: int = 1) -> MagicMock:
    tracks = []
    for i in range(with_previews):
        tracks.append({
            "id": f"track_{i}",
            "name": f"Song {i}",
            "preview_url": f"https://example.com/preview_{i}.mp3",
            "artists": [{"name": "Coldplay"}],
            "album": {"name": "Album X"},
        })
    for i in range(without_previews):
        tracks.append({
            "id": f"no_preview_{i}",
            "name": f"No Preview Song {i}",
            "preview_url": None,
            "artists": [{"name": "Coldplay"}],
            "album": {"name": "Album Y"},
        })
    return _mock_response(200, {"tracks": tracks})


# ── Auth tests ─────────────────────────────────────────────────────────────

class TestAuth:
    def test_raises_on_empty_credentials(self):
        try:
            SpotifyService("", "")
            assert False, "Should have raised"
        except SpotifyAuthError:
            pass

    def test_raises_on_missing_client_id(self):
        try:
            SpotifyService("", "secret")
            assert False, "Should have raised"
        except SpotifyAuthError:
            pass

    @patch("spotify_service.requests.post")
    def test_token_request_called_with_correct_args(self, mock_post):
        mock_post.return_value = _token_response()
        svc = SpotifyService("my_id", "my_secret")
        svc._get_token()
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "grant_type" in call_kwargs.kwargs.get("data", {}) or \
               "grant_type" in (call_kwargs.args[1] if len(call_kwargs.args) > 1 else {})

    @patch("spotify_service.requests.post")
    def test_bad_token_response_raises(self, mock_post):
        mock_post.return_value = _mock_response(401, {"error": "Unauthorized"})
        svc = SpotifyService("bad_id", "bad_secret")
        try:
            svc._get_token()
            assert False, "Should have raised SpotifyAuthError"
        except SpotifyAuthError:
            pass


# ── Artist resolution tests ────────────────────────────────────────────────

class TestArtistResolution:
    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_resolves_artist_id(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _artist_search_response("artist_xyz")
        svc = SpotifyService("id", "secret")
        result = svc._resolve_artist_id("Coldplay")
        assert result == "artist_xyz"

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_caches_artist_id(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _artist_search_response("artist_xyz")
        svc = SpotifyService("id", "secret")
        svc._resolve_artist_id("Coldplay")
        svc._resolve_artist_id("Coldplay")   # second call should use cache
        assert mock_get.call_count == 1      # only one HTTP call made

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_none_for_unknown_artist(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response(200, {"artists": {"items": []}})
        svc = SpotifyService("id", "secret")
        result = svc._resolve_artist_id("DefinitelyNotARealArtist99999")
        assert result is None


# ── Top tracks tests ───────────────────────────────────────────────────────

class TestTopTracks:
    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_only_tracks_with_previews(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        # First call: artist search, second call: top tracks
        mock_get.side_effect = [
            _artist_search_response(),
            _top_tracks_response(with_previews=3, without_previews=2),
        ]
        svc = SpotifyService("id", "secret")
        tracks = svc.get_artist_top_tracks("Coldplay")
        assert len(tracks) == 3
        assert all(t.has_preview for t in tracks)

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_empty_for_unresolvable_artist(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response(200, {"artists": {"items": []}})
        svc = SpotifyService("id", "secret")
        tracks = svc.get_artist_top_tracks("NotARealArtist")
        assert tracks == []

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_track_info_fields_populated(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.side_effect = [
            _artist_search_response("a1"),
            _top_tracks_response(with_previews=1, without_previews=0),
        ]
        svc = SpotifyService("id", "secret")
        tracks = svc.get_artist_top_tracks("Coldplay")
        t = tracks[0]
        assert t.track_id == "track_0"
        assert t.title == "Song 0"
        assert t.artist == "Coldplay"
        assert t.preview_url.startswith("https://")
        assert t.source == "Coldplay"


# ── Random track selection tests ───────────────────────────────────────────

class TestRandomTrack:
    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_track_from_pool(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.side_effect = [
            _artist_search_response("a1"),
            _top_tracks_response(with_previews=2),
        ]
        svc = SpotifyService("id", "secret")
        track = svc.get_random_track_by_artist(["Coldplay"])
        assert track is not None
        assert isinstance(track, TrackInfo)

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_respects_excluded_ids(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.side_effect = [
            _artist_search_response("a1"),
            _top_tracks_response(with_previews=1),    # only track_0
        ]
        svc = SpotifyService("id", "secret")
        track = svc.get_random_track_by_artist(["Coldplay"], exclude_ids={"track_0"})
        # track_0 is excluded and it's the only one → should return None
        assert track is None

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_none_when_pool_empty(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.side_effect = [
            _mock_response(200, {"artists": {"items": []}}),  # artist not found
        ]
        svc = SpotifyService("id", "secret")
        track = svc.get_random_track_by_artist(["NotRealArtist"])
        assert track is None


# ── fetch_rounds integration tests ────────────────────────────────────────

class TestFetchRounds:
    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_returns_correct_count(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        # Provide enough responses: each round needs artist search + top tracks
        # We request 2 rounds from 2 different artists
        mock_get.side_effect = [
            _artist_search_response("a1"),
            _top_tracks_response(with_previews=5),
            _artist_search_response("a2"),
            _top_tracks_response(with_previews=5),
        ] * 5   # repeat to cover multiple get_random_track_by_artist calls
        svc = SpotifyService("id", "secret")
        tracks = svc.fetch_rounds(["Coldplay", "Adele"], count=2)
        assert len(tracks) == 2

    @patch("spotify_service.requests.get")
    @patch("spotify_service.requests.post")
    def test_raises_when_not_enough_tracks(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        # Artist search returns nothing → zero tracks available
        mock_get.return_value = _mock_response(200, {"artists": {"items": []}})
        svc = SpotifyService("id", "secret")
        try:
            svc.fetch_rounds(["FakeArtist"], count=3)
            assert False, "Should have raised SpotifyFetchError"
        except SpotifyFetchError as exc:
            assert "previewable tracks" in str(exc).lower() or \
                   "found" in str(exc).lower()

    def test_raises_on_empty_artist_list(self):
        svc = SpotifyService("id", "secret")
        try:
            svc.fetch_rounds([], count=1)
            assert False, "Should have raised"
        except SpotifyFetchError:
            pass
