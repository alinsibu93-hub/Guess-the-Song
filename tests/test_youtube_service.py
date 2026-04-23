"""
tests/test_youtube_service.py — Unit tests for YouTubeService, scoring, and selection.

All YouTube HTTP calls are mocked — no real API key needed.
Run with:  python -m pytest tests/ -v
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from youtube_service import (
    YouTubeService, TrackInfo,
    YouTubeAuthError, YouTubeFetchError, YouTubeQuotaError,
    _is_blacklisted, _score_video, select_best_youtube_video,
    _generate_choices,
)


# ── Test data builders ───────────────────────────────────────────────────────


def _make_item(
    video_id: str,
    yt_title: str,
    channel: str = "Artist Channel",
) -> dict:
    """Build a raw YouTube API search result item."""
    return {
        "id": {"videoId": video_id},
        "snippet": {
            "title": yt_title,
            "channelTitle": channel,
            "thumbnails": {"default": {"url": f"https://img.youtube.com/vi/{video_id}/default.jpg"}},
        },
    }


def _mock_response(status_code: int, body: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.content = json.dumps(body).encode()
    resp.raise_for_status = MagicMock(
        side_effect=None if status_code < 400 else Exception(f"HTTP {status_code}")
    )
    return resp


def _search_resp(*items: dict) -> MagicMock:
    """Wrap item dicts in a 200 YouTube search response mock."""
    return _mock_response(200, {"items": list(items)})


def _empty_resp() -> MagicMock:
    return _mock_response(200, {"items": []})


_SAMPLE_LIBRARY = [
    ("Adele", "Hello"),
    ("Coldplay", "Yellow"),
    ("Queen", "Bohemian Rhapsody"),
    ("Ed Sheeran", "Shape of You"),
    ("Daft Punk", "Get Lucky"),
]


# ── _is_blacklisted ──────────────────────────────────────────────────────────


class TestIsBlacklisted:
    def test_live_disqualifies(self):
        assert _is_blacklisted("Ed Sheeran - Shape of You (Live at Wembley)")

    def test_lyric_disqualifies(self):
        assert _is_blacklisted("Shape of You - Lyric Video")

    def test_lyrics_disqualifies(self):
        assert _is_blacklisted("Shape of You lyrics")

    def test_karaoke_disqualifies(self):
        assert _is_blacklisted("Shape of You (Karaoke Version)")

    def test_cover_disqualifies(self):
        assert _is_blacklisted("Shape of You - Guitar Cover")

    def test_instrumental_disqualifies(self):
        assert _is_blacklisted("Shape of You Instrumental")

    def test_remix_disqualifies(self):
        assert _is_blacklisted("Shape of You (DJ Remix)")

    def test_case_insensitive(self):
        assert _is_blacklisted("Shape of You LIVE 2018")
        assert _is_blacklisted("Shape of You KARAOKE")

    def test_official_audio_not_blacklisted(self):
        assert not _is_blacklisted("Ed Sheeran - Shape of You (Official Audio)")

    def test_official_music_video_not_blacklisted(self):
        assert not _is_blacklisted("Ed Sheeran - Shape of You (Official Music Video)")

    def test_believe_not_blacklisted(self):
        # "live" must not match inside "believe" — word boundary check
        assert not _is_blacklisted("Believe - Cher Official Audio")

    def test_olivia_not_blacklisted(self):
        # "via" inside "Olivia" must not be matched
        assert not _is_blacklisted("One Direction - Olivia (Audio)")

    def test_deliver_not_blacklisted(self):
        # "live" inside "deliver" — must not match
        assert not _is_blacklisted("Adele - Deliver (Official Audio)")

    def test_empty_title_not_blacklisted(self):
        assert not _is_blacklisted("")


# ── _score_video ──────────────────────────────────────────────────────────────


class TestScoreVideo:
    def test_official_audio_with_artist_and_track_scores_high(self):
        score = _score_video(
            "Ed Sheeran - Shape of You (Official Audio)",
            "Ed Sheeran",
            "Ed Sheeran",
            "Shape of You",
        )
        # artist(+3) + track(+3) + official(+2) + audio(+1) + channel_artist(+2) = 11
        assert score == 11

    def test_official_music_video_scores_well(self):
        score = _score_video(
            "Ed Sheeran - Shape of You (Official Music Video)",
            "Ed Sheeran",
            "Ed Sheeran",
            "Shape of You",
        )
        # artist(+3) + track(+3) + official(+2) + music video(+1) + channel(+2) = 11
        assert score == 11

    def test_artist_in_title_adds_points(self):
        s_with = _score_video("Ed Sheeran - Shape of You", "X", "Ed Sheeran", "Shape of You")
        s_without = _score_video("Shape of You Song", "X", "Ed Sheeran", "Shape of You")
        assert s_with > s_without

    def test_track_in_title_adds_points(self):
        s_with = _score_video("Shape of You Official", "X", "Ed Sheeran", "Shape of You")
        s_without = _score_video("Ed Sheeran New Song", "X", "Ed Sheeran", "Shape of You")
        assert s_with > s_without

    def test_official_keyword_adds_points(self):
        s_with = _score_video("Shape of You Official Audio", "X", "Ed Sheeran", "Shape of You")
        s_without = _score_video("Shape of You Audio", "X", "Ed Sheeran", "Shape of You")
        assert s_with > s_without

    def test_channel_name_match_adds_points(self):
        s_with = _score_video("Shape of You", "Ed Sheeran", "Ed Sheeran", "Shape of You")
        s_without = _score_video("Shape of You", "VEVO Channel", "Ed Sheeran", "Shape of You")
        assert s_with > s_without

    def test_ambiguous_terms_subtract_points(self):
        s_clean = _score_video("Shape of You Official Audio", "X", "Ed Sheeran", "Shape of You")
        s_acoustic = _score_video("Shape of You Acoustic Version", "X", "Ed Sheeran", "Shape of You")
        assert s_clean > s_acoustic

    def test_multiple_ambiguous_terms_stack(self):
        s_one = _score_video("Shape of You Acoustic", "X", "Ed Sheeran", "Shape of You")
        s_two = _score_video("Shape of You Acoustic Extended", "X", "Ed Sheeran", "Shape of You")
        assert s_one > s_two

    def test_case_insensitive(self):
        s_lower = _score_video("ed sheeran shape of you official audio", "ed sheeran", "Ed Sheeran", "Shape of You")
        s_upper = _score_video("ED SHEERAN SHAPE OF YOU OFFICIAL AUDIO", "Ed Sheeran", "Ed Sheeran", "Shape of You")
        assert s_lower == s_upper

    def test_zero_score_for_unrelated_video(self):
        score = _score_video("Random Cooking Video", "RandomChannel", "Ed Sheeran", "Shape of You")
        assert score == 0


# ── select_best_youtube_video ─────────────────────────────────────────────────


class TestSelectBestYouTubeVideo:
    def test_returns_none_for_empty_items(self):
        result = select_best_youtube_video([], "Ed Sheeran", "Shape of You")
        assert result is None

    def test_returns_official_over_karaoke(self):
        items = [
            _make_item("k1", "Shape of You Karaoke Version"),
            _make_item("o1", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran"),
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You")
        assert result is not None
        assert result["id"]["videoId"] == "o1"

    def test_filters_live_version(self):
        items = [
            _make_item("l1", "Shape of You Live at Wembley"),
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You", allow_blacklisted_fallback=False)
        assert result is None

    def test_fallback_returns_blacklisted_when_nothing_else(self):
        items = [
            _make_item("l1", "Shape of You Lyric Video"),
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You", allow_blacklisted_fallback=True)
        assert result is not None
        assert result["id"]["videoId"] == "l1"

    def test_picks_highest_scoring_among_multiple_clean(self):
        items = [
            _make_item("a1", "Shape of You (Acoustic)"),          # -1 ambiguous
            _make_item("a2", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran"),  # best
            _make_item("a3", "Shape of You"),                      # less signals
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You")
        assert result["id"]["videoId"] == "a2"

    def test_ignores_blacklisted_when_clean_available(self):
        items = [
            _make_item("b1", "Shape of You Karaoke"),              # blacklisted
            _make_item("c1", "Ed Sheeran Shape of You Official"),  # clean
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You")
        assert result["id"]["videoId"] == "c1"

    def test_all_blacklisted_no_fallback_returns_none(self):
        items = [
            _make_item("b1", "Shape of You Karaoke"),
            _make_item("b2", "Shape of You Lyrics"),
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You", allow_blacklisted_fallback=False)
        assert result is None

    def test_all_blacklisted_with_fallback_returns_best_scoring(self):
        items = [
            _make_item("b1", "Shape of You Lyrics"),
            _make_item("b2", "Ed Sheeran Shape of You Karaoke", "Ed Sheeran"),  # higher score among blacklisted
        ]
        result = select_best_youtube_video(items, "Ed Sheeran", "Shape of You", allow_blacklisted_fallback=True)
        assert result is not None
        assert result["id"]["videoId"] == "b2"


# ── Auth tests ───────────────────────────────────────────────────────────────


class TestAuth:
    def test_raises_on_empty_api_key(self):
        try:
            YouTubeService("")
            assert False, "Should have raised YouTubeAuthError"
        except YouTubeAuthError:
            pass

    def test_accepts_valid_key(self):
        svc = YouTubeService("valid_key")
        assert svc.api_key == "valid_key"


# ── search_video tests ───────────────────────────────────────────────────────


class TestSearchVideo:
    @patch("youtube_service.requests.get")
    def test_returns_best_matching_result(self, mock_get):
        item = _make_item("JGwWNGJdvx8", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        result = svc.search_video("Ed Sheeran", "Shape of You")
        assert result is not None
        assert isinstance(result, TrackInfo)
        assert result.video_id == "JGwWNGJdvx8"
        assert result.title == "Shape of You"
        assert result.artist == "Ed Sheeran"

    @patch("youtube_service.requests.get")
    def test_returns_none_when_both_passes_empty(self, mock_get):
        mock_get.return_value = _empty_resp()
        svc = YouTubeService("key")
        result = svc.search_video("Unknown Artist", "Unknown Song")
        assert result is None

    @patch("youtube_service.requests.get")
    def test_selects_official_over_karaoke_in_same_result_set(self, mock_get):
        karaoke = _make_item("k1", "Shape of You Karaoke Version")
        official = _make_item("o1", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran")
        mock_get.return_value = _search_resp(karaoke, official)
        svc = YouTubeService("key")
        result = svc.search_video("Ed Sheeran", "Shape of You")
        assert result.video_id == "o1"

    @patch("youtube_service.requests.get")
    def test_fallback_triggered_when_primary_all_blacklisted(self, mock_get):
        """Primary returns only karaoke; fallback returns official."""
        primary_karaoke = _make_item("k1", "Shape of You Karaoke Version")
        fallback_official = _make_item("o1", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran")
        mock_get.side_effect = [
            _search_resp(primary_karaoke),   # Pass 1: all blacklisted → no result
            _search_resp(fallback_official), # Pass 2: clean result found
        ]
        svc = YouTubeService("key")
        result = svc.search_video("Ed Sheeran", "Shape of You")
        assert result is not None
        assert result.video_id == "o1"
        assert mock_get.call_count == 2  # confirms fallback was triggered

    @patch("youtube_service.requests.get")
    def test_no_fallback_when_primary_succeeds(self, mock_get):
        """Primary finds a clean result → Pass 2 never executes."""
        official = _make_item("o1", "Ed Sheeran - Shape of You (Official Audio)", "Ed Sheeran")
        mock_get.return_value = _search_resp(official)
        svc = YouTubeService("key")
        svc.search_video("Ed Sheeran", "Shape of You")
        assert mock_get.call_count == 1  # only 1 HTTP call made

    @patch("youtube_service.requests.get")
    def test_returns_blacklisted_as_last_resort(self, mock_get):
        """Both passes have only blacklisted results — fallback pass returns best of them."""
        blacklisted_primary = _make_item("k1", "Shape of You Karaoke")
        blacklisted_fallback = _make_item("k2", "Ed Sheeran Shape of You Lyric", "Ed Sheeran")
        mock_get.side_effect = [
            _search_resp(blacklisted_primary),  # Pass 1: all blacklisted
            _search_resp(blacklisted_fallback), # Pass 2: all blacklisted → use best
        ]
        svc = YouTubeService("key")
        result = svc.search_video("Ed Sheeran", "Shape of You")
        assert result is not None
        assert result.video_id == "k2"  # higher score (artist in channel)

    @patch("youtube_service.requests.get")
    def test_raises_fetch_error_on_network_failure(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("connection error")
        svc = YouTubeService("key")
        try:
            svc.search_video("Artist", "Title")
            assert False, "Should have raised YouTubeFetchError"
        except YouTubeFetchError:
            pass

    @patch("youtube_service.requests.get")
    def test_raises_quota_error_on_403_quota_exceeded(self, mock_get):
        mock_get.return_value = _mock_response(403, {
            "error": {"code": 403, "errors": [{"reason": "quotaExceeded"}]}
        })
        svc = YouTubeService("key")
        try:
            svc.search_video("Artist", "Title")
            assert False, "Should have raised YouTubeQuotaError"
        except YouTubeQuotaError:
            pass

    @patch("youtube_service.requests.get")
    def test_raises_auth_error_on_403_forbidden(self, mock_get):
        mock_get.return_value = _mock_response(403, {
            "error": {"code": 403, "errors": [{"reason": "forbidden"}]}
        })
        svc = YouTubeService("bad_key")
        try:
            svc.search_video("Artist", "Title")
            assert False, "Should have raised YouTubeAuthError"
        except YouTubeAuthError:
            pass

    @patch("youtube_service.requests.get")
    def test_api_key_sent_in_params(self, mock_get):
        item = _make_item("v1", "Song Official Audio")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("my_secret_key")
        svc.search_video("Artist", "Title")
        params = mock_get.call_args[1].get("params", {})
        assert params.get("key") == "my_secret_key"

    @patch("youtube_service.requests.get")
    def test_music_category_filter_in_params(self, mock_get):
        item = _make_item("v1", "Song Official Audio")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        svc.search_video("Artist", "Title")
        params = mock_get.call_args[1].get("params", {})
        assert params.get("videoCategoryId") == "10"

    @patch("youtube_service.requests.get")
    def test_max_results_is_at_least_5(self, mock_get):
        item = _make_item("v1", "Song Official Audio")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        svc.search_video("Artist", "Title")
        params = mock_get.call_args[1].get("params", {})
        assert params.get("maxResults", 0) >= 5

    @patch("youtube_service.requests.get")
    def test_thumbnail_populated(self, mock_get):
        item = _make_item("vid", "Artist - Song Official")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        result = svc.search_video("Artist", "Song")
        assert result is not None
        assert result.thumbnail is not None
        assert result.thumbnail.startswith("https://")


# ── _generate_choices tests ──────────────────────────────────────────────────


class TestGenerateChoices:
    def test_returns_correct_count(self):
        choices = _generate_choices("Shape of You", "Ed Sheeran", _SAMPLE_LIBRARY, count=4)
        assert len(choices) == 4

    def test_correct_answer_included(self):
        choices = _generate_choices("Shape of You", "Ed Sheeran", _SAMPLE_LIBRARY, count=4)
        assert any(c["title"] == "Shape of You" and c["artist"] == "Ed Sheeran" for c in choices)

    def test_no_duplicate_entries(self):
        choices = _generate_choices("Yellow", "Coldplay", _SAMPLE_LIBRARY, count=4)
        seen = set()
        for c in choices:
            key = (c["title"], c["artist"])
            assert key not in seen, f"Duplicate: {key}"
            seen.add(key)

    def test_choices_have_required_fields(self):
        choices = _generate_choices("Hello", "Adele", _SAMPLE_LIBRARY, count=4)
        for c in choices:
            assert "title" in c and "artist" in c

    def test_fewer_choices_when_library_too_small(self):
        tiny = [("Adele", "Hello"), ("Coldplay", "Yellow")]
        choices = _generate_choices("Hello", "Adele", tiny, count=4)
        assert len(choices) == 2  # 1 distractor + 1 correct

    def test_correct_answer_not_duplicated(self):
        choices = _generate_choices("Yellow", "Coldplay", _SAMPLE_LIBRARY, count=4)
        correct_count = sum(
            1 for c in choices if c["title"] == "Yellow" and c["artist"] == "Coldplay"
        )
        assert correct_count == 1


# ── fetch_rounds tests ────────────────────────────────────────────────────────


class TestFetchRounds:
    @patch("youtube_service.requests.get")
    def test_returns_correct_count(self, mock_get):
        mock_get.side_effect = [
            _search_resp(_make_item("id1", "Artist A - Song 1 Official Audio", "Artist A")),
            _search_resp(_make_item("id2", "Artist B - Song 2 Official Audio", "Artist B")),
            _search_resp(_make_item("id3", "Artist C - Song 3 Official Audio", "Artist C")),
        ]
        svc = YouTubeService("key")
        library = [("Artist A", "Song 1"), ("Artist B", "Song 2"), ("Artist C", "Song 3")]
        rounds = svc.fetch_rounds(library, count=3, choices_count=3)
        assert len(rounds) == 3

    @patch("youtube_service.requests.get")
    def test_round_has_required_fields(self, mock_get):
        item = _make_item("vid999", "Artist - Title Official Audio", "Artist")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        rounds = svc.fetch_rounds([("Artist", "Title")], count=1, choices_count=1)
        r = rounds[0]
        for field in ("title", "artist", "videoId", "startTime", "duration", "choices"):
            assert field in r, f"Missing: {field}"
        assert r["videoId"] == "vid999"

    @patch("youtube_service.requests.get")
    def test_choices_contain_correct_answer(self, mock_get):
        library = list(_SAMPLE_LIBRARY)
        item = _make_item("v1", "Adele - Hello (Official Audio)", "Adele")
        mock_get.return_value = _search_resp(item)
        svc = YouTubeService("key")
        rounds = svc.fetch_rounds(library, count=1)
        r = rounds[0]
        assert any(c["title"] == r["title"] and c["artist"] == r["artist"] for c in r["choices"])

    @patch("youtube_service.requests.get")
    def test_start_time_in_valid_range(self, mock_get):
        clip_duration = 8
        mock_get.return_value = _search_resp(_make_item("v1", "Song Official Audio"))
        svc = YouTubeService("key")
        rounds = svc.fetch_rounds([("Artist", "Title")], count=1, choices_count=1, clip_duration=clip_duration)
        expected_max = max(31, 90 - clip_duration)
        assert 30 <= rounds[0]["startTime"] <= expected_max

    @patch("youtube_service.requests.get")
    def test_duration_equals_clip_duration(self, mock_get):
        mock_get.return_value = _search_resp(_make_item("v1", "Song Official Audio"))
        svc = YouTubeService("key")
        for clip_dur in (3, 8, 15):
            rounds = svc.fetch_rounds([("Artist", "Title")], count=1, choices_count=1, clip_duration=clip_dur)
            assert rounds[0]["duration"] == clip_dur

    @patch("youtube_service.requests.get")
    def test_raises_when_not_enough_tracks(self, mock_get):
        mock_get.return_value = _empty_resp()
        svc = YouTubeService("key")
        try:
            svc.fetch_rounds(_SAMPLE_LIBRARY, count=len(_SAMPLE_LIBRARY) + 1)
            assert False, "Should have raised YouTubeFetchError"
        except YouTubeFetchError as exc:
            assert "only find" in str(exc).lower()

    def test_raises_on_empty_library(self):
        svc = YouTubeService("key")
        try:
            svc.fetch_rounds([], count=1)
            assert False
        except YouTubeFetchError:
            pass

    def test_raises_on_library_smaller_than_choices_count(self):
        svc = YouTubeService("key")
        try:
            svc.fetch_rounds([("A", "B"), ("C", "D")], count=1, choices_count=4)
            assert False, "Should have raised YouTubeFetchError"
        except YouTubeFetchError as exc:
            assert "choices_count" in str(exc)

    @patch("youtube_service.requests.get")
    def test_deduplicates_video_ids(self, mock_get):
        # Both songs resolve to the same videoId
        mock_get.return_value = _search_resp(_make_item("same_id", "Song Official Audio"))
        svc = YouTubeService("key")
        library = [("Artist A", "Song 1"), ("Artist B", "Song 2")]
        try:
            svc.fetch_rounds(library, count=2)
            assert False
        except YouTubeFetchError:
            pass
