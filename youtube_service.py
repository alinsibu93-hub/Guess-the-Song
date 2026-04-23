"""
youtube_service.py — YouTube Data API v3 integration for Guess the Song.

Video selection strategy (two-pass):
  Pass 1 — "{artist} {title} official audio", maxResults=5
            Blacklisted results (live/lyric/karaoke/cover/remix/instrumental)
            are excluded. Best-scoring remaining result is returned.
  Pass 2 — "{artist} {title}", maxResults=5  (fallback)
            Same scoring, but if ALL results are blacklisted the best one
            is returned anyway — better than giving up entirely.

No audio download — playback is client-side via YouTube IFrame Player API.
"""

import re
import random
import requests
from dataclasses import dataclass
from typing import List, Optional, Tuple

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

_START_MIN = 30        # Minimum start time in seconds (skips most intros)
_START_MAX = 90        # Maximum start time in seconds
_SEARCH_MAX_RESULTS = 5  # Candidates fetched per query — balances cost vs. choice

# Terms that categorically disqualify a result for a "guess the song" game.
# Word-boundary anchored: "believe" does NOT match "live", "Olivia" does NOT match "via".
_BLACKLIST_RE = re.compile(
    r"\b(?:live|lyric|lyrics|karaoke|cover|instrumental|remix)\b",
    re.IGNORECASE,
)

# Non-standard variants — present but not immediately disqualifying.
# Each term subtracts 1 point from the score.
_AMBIGUOUS_TERMS = ("acoustic", "version", "remaster", "remastered", "extended", "edit")


# ── Data classes & exceptions ──────────────────────────────────────────────


@dataclass(frozen=True)
class TrackInfo:
    title: str
    artist: str
    video_id: str
    thumbnail: Optional[str] = None


class YouTubeAuthError(Exception):
    pass


class YouTubeFetchError(Exception):
    pass


class YouTubeQuotaError(YouTubeFetchError):
    """Raised when the YouTube Data API daily quota is exceeded."""
    pass


# ── Filtering & scoring ────────────────────────────────────────────────────


def _is_blacklisted(yt_title: str) -> bool:
    """
    Return True if the YouTube video title contains a disqualifying term.

    Uses word boundaries so partial matches inside other words are ignored:
      "believe"  → does NOT match \\blive\\b  ✓
      "Olivia"   → does NOT match \\bvia\\b   ✓
      "LIVE Tour" → MATCHES \\blive\\b        ✓
    """
    return bool(_BLACKLIST_RE.search(yt_title))


def _score_video(yt_title: str, channel_title: str, artist: str, track: str) -> int:
    """
    Score a YouTube result for relevance to (artist, track). Higher is better.

    Positive signals:
      +3  title contains artist name (substring, case-insensitive)
      +3  title contains track name  (substring, case-insensitive)
      +2  title contains "official"  → canonical upload signal
      +1  title contains "audio"    → non-lyric audio rip
      +1  title contains "music video"
      +2  channel name contains artist name → strong proxy for official channel

    Negative signals:
      -1  per ambiguous term (acoustic, version, remaster, remastered, extended, edit)

    Trade-offs:
      - Substring matching means "Ed Sheeran" matches "Ed Sheeran Vevo" channel. Intended.
      - "official" in title is a soft signal — some unofficial uploads use it too.
      - Channel name check is best available heuristic without the YouTube Channels API.
    """
    t = yt_title.lower()
    ch = channel_title.lower()
    a = artist.lower()
    k = track.lower()

    score = 0

    if a in t:
        score += 3
    if k in t:
        score += 3
    if "official" in t:
        score += 2
    if "audio" in t:
        score += 1
    if "music video" in t:
        score += 1
    if a in ch:
        score += 2

    for term in _AMBIGUOUS_TERMS:
        if term in t:
            score -= 1

    return score


def select_best_youtube_video(
    items: List[dict],
    artist: str,
    track: str,
    allow_blacklisted_fallback: bool = True,
) -> Optional[dict]:
    """
    Given a list of raw YouTube search result items (snippet format), filter and
    return the best match for (artist, track).

    Algorithm:
      1. Partition items into clean (non-blacklisted) and blacklisted.
      2. If clean pool is non-empty → pick highest-scoring item from clean pool.
      3. If clean pool is empty:
           - allow_blacklisted_fallback=True  → pick best from blacklisted pool.
           - allow_blacklisted_fallback=False → return None (caller tries next query).
      4. Return None if items is empty.

    This function is pure — no I/O, deterministic given the same inputs.
    Easy to unit-test by constructing item dicts directly.
    """
    if not items:
        return None

    clean: List[dict] = []
    blacklisted: List[dict] = []

    for item in items:
        yt_title = item.get("snippet", {}).get("title", "")
        (blacklisted if _is_blacklisted(yt_title) else clean).append(item)

    pool = clean or (blacklisted if allow_blacklisted_fallback else [])
    if not pool:
        return None

    def _key(item: dict) -> int:
        s = item.get("snippet", {})
        return _score_video(s.get("title", ""), s.get("channelTitle", ""), artist, track)

    return max(pool, key=_key)


# ── Service ────────────────────────────────────────────────────────────────


class YouTubeService:
    def __init__(self, api_key: str):
        if not api_key:
            raise YouTubeAuthError(
                "YOUTUBE_API_KEY is missing. "
                "Set it in your .env file or as an environment variable."
            )
        self.api_key = api_key

    def _fetch_items(self, query: str, max_results: int = _SEARCH_MAX_RESULTS) -> List[dict]:
        """
        Execute a YouTube Data API v3 search and return the raw items list.
        Raises YouTubeAuthError, YouTubeQuotaError, or YouTubeFetchError on failure.
        """
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoCategoryId": "10",  # Music category
            "maxResults": max_results,
            "key": self.api_key,
        }
        try:
            resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        except requests.RequestException as exc:
            raise YouTubeFetchError(f"YouTube API network error: {exc}") from exc

        if resp.status_code == 403:
            body = resp.json() if resp.content else {}
            reason = (
                body.get("error", {})
                    .get("errors", [{}])[0]
                    .get("reason", "")
            )
            if reason == "quotaExceeded":
                raise YouTubeQuotaError(
                    "YouTube Data API daily quota exceeded. "
                    "Wait until midnight Pacific time or request a quota increase."
                )
            raise YouTubeAuthError(
                "YouTube API returned 403. Check that your API key is valid "
                "and the YouTube Data API v3 is enabled in Google Cloud Console."
            )

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise YouTubeFetchError(f"YouTube API error {resp.status_code}: {exc}") from exc

        return resp.json().get("items", [])

    def search_video(self, artist: str, title: str) -> Optional[TrackInfo]:
        """
        Search YouTube for (artist, title) using a two-pass strategy.

        Pass 1 — query: "{artist} {title} official audio"
          Strict: blacklisted results are excluded.
          Returns the highest-scoring non-blacklisted item.
          Proceeds to Pass 2 only if the clean pool is empty.

        Pass 2 (fallback) — query: "{artist} {title}"
          Lenient: if ALL results are blacklisted, returns the best blacklisted
          item rather than returning None.

        Returns None only when both passes yield zero items with a videoId.
        An API error (auth, quota, network) raises immediately — no retry.
        """
        for query, allow_blacklisted_fallback in (
            (f"{artist} {title} official audio", False),
            (f"{artist} {title}", True),
        ):
            items = self._fetch_items(query)
            best = select_best_youtube_video(items, artist, title, allow_blacklisted_fallback)
            if best is not None:
                return _item_to_track_info(best, title, artist)

        return None

    def fetch_rounds(
        self,
        song_library: List[Tuple[str, str]],
        count: int,
        choices_count: int = 4,
        clip_duration: int = 8,
    ) -> List[dict]:
        """
        Resolve `count` unique (artist, title) pairs from song_library via YouTube.

        Returns a list of round dicts:
          { title, artist, videoId, startTime, duration, thumbnail, choices }

        YouTube search quota cost: each song requires 1–2 search calls (two-pass
        strategy). At 100 quota units per call, a 20-round game costs up to
        4 000 units. The free daily quota is 10 000 units (~2–5 games/day).
        """
        if not song_library:
            raise YouTubeFetchError("song_library is empty — nothing to search for.")
        if len(song_library) < choices_count:
            raise YouTubeFetchError(
                f"song_library has {len(song_library)} songs but choices_count={choices_count} "
                f"requires at least {choices_count}. Add more songs or reduce choices_count."
            )

        candidates = list(song_library)
        random.shuffle(candidates)

        seen_ids: set = set()
        rounds: List[dict] = []

        for artist, title in candidates:
            if len(rounds) >= count:
                break
            track = self.search_video(artist, title)
            if track is None or track.video_id in seen_ids:
                continue
            seen_ids.add(track.video_id)
            # Cap startTime so startTime + clip_duration never overruns a typical
            # 3-minute song. _START_MAX is the ceiling before adjustment.
            start_max = max(_START_MIN + 1, _START_MAX - clip_duration)
            rounds.append({
                "title": track.title,
                "artist": track.artist,
                "videoId": track.video_id,
                "startTime": random.randint(_START_MIN, start_max),
                "duration": clip_duration,
                "thumbnail": track.thumbnail,
                "choices": _generate_choices(
                    track.title, track.artist, song_library, choices_count
                ),
            })

        if len(rounds) < count:
            raise YouTubeFetchError(
                f"Could only find {len(rounds)} tracks from YouTube, needed {count}. "
                "Check your API key or expand the song library."
            )

        return rounds


# ── Helpers ────────────────────────────────────────────────────────────────


def _item_to_track_info(item: dict, title: str, artist: str) -> Optional[TrackInfo]:
    """Convert a raw YouTube search result item to a TrackInfo, or None."""
    video_id = item.get("id", {}).get("videoId")
    if not video_id:
        return None
    thumbnails = item.get("snippet", {}).get("thumbnails", {})
    thumbnail = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )
    return TrackInfo(title=title, artist=artist, video_id=video_id, thumbnail=thumbnail)


def _generate_choices(
    correct_title: str,
    correct_artist: str,
    song_library: List[Tuple[str, str]],
    count: int = 4,
) -> List[dict]:
    """
    Build a shuffled list of `count` choices that includes the correct answer.
    Wrong options are drawn from song_library.
    """
    distractors = [
        {"title": t, "artist": a}
        for a, t in song_library
        if not (t == correct_title and a == correct_artist)
    ]
    random.shuffle(distractors)

    n_wrong = min(count - 1, len(distractors))
    choices = distractors[:n_wrong]
    choices.append({"title": correct_title, "artist": correct_artist})
    random.shuffle(choices)
    return choices
