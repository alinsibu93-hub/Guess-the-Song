"""
itunes_service.py — iTunes Search API integration for Guess the Song.

Why iTunes?
  Unlike YouTube IFrame (which runs inside a cross-origin iframe governed by
  Chrome's autoplay policy), iTunes previews are raw .m4a URLs served over
  HTTPS. They play in a native <audio> element with zero autoplay headaches.

API specifics:
  https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/
  - No authentication, no quotas (soft limit ~20 req/min per IP)
  - previewUrl is a 30-second clip, almost always the chorus/hook
  - artworkUrl100 can be upgraded to 300x300 / 600x600 by string replace
"""

import random
import re
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

# Minimum pool size before triggering genre/era fallback logic.
# Needs to comfortably cover `count` rounds + distractor generation.
_MIN_POOL = 12


# ── Data classes & exceptions ──────────────────────────────────────────────


@dataclass(frozen=True)
class TrackInfo:
    title: str
    artist: str
    preview_url: str
    artwork_url: Optional[str] = None


class iTunesFetchError(Exception):
    pass


# ── Helpers ────────────────────────────────────────────────────────────────


def _normalize(text: str) -> str:
    """Lowercase + strip punctuation for fuzzy title comparison."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _title_close(actual: str, expected: str) -> bool:
    """
    Substring-based fuzzy match. Handles common title variations:
      "Shape of You"         vs "Shape of You (Stormzy Remix)"  → match
      "Get Lucky (Radio Edit)" vs "Get Lucky"                    → match
      "Believer"               vs "Thunder"                      → no match
    """
    a, e = _normalize(actual), _normalize(expected)
    if not a or not e:
        return False
    return e in a or a in e


def _upgrade_artwork(url: str) -> str:
    """
    Apple's CDN lets you request higher-res artwork by swapping the size
    token in the URL. 100x100 is the default; 300x300 looks great on cards.
    """
    return url.replace("100x100", "300x300") if url else url


def _item_to_track_info(item: dict, title: str, artist: str) -> Optional[TrackInfo]:
    preview_url = item.get("previewUrl")
    if not preview_url:
        return None
    artwork = _upgrade_artwork(item.get("artworkUrl100", "") or "")
    return TrackInfo(
        title=title,
        artist=artist,
        preview_url=preview_url,
        artwork_url=artwork or None,
    )


# ── Song pool filtering ────────────────────────────────────────────────────


def _build_song_pool(
    song_library: List[Dict[str, str]],
    genres: Optional[List[str]],
    eras: Optional[List[str]],
    count: int,
    choices_count: int,
    related_genres_map: Dict[str, List[str]],
) -> List[Dict[str, str]]:
    """
    Return a candidate pool from song_library that satisfies the genre/era
    filter, with progressive fallback when the pool is too small.

    Minimum needed: enough to play `count` rounds AND generate `choices_count`
    distractors. We use _MIN_POOL as a floor for robustness against iTunes
    lookup failures.

    Fallback order:
      1. Songs matching BOTH selected genres AND selected eras  (exact)
      2. Add songs from related genres, keeping era filter      (related genres)
      3. Remove era filter, keep original genre filter          (genre-only)
      4. Full library                                           (no filter)
    """
    min_needed = max(count + choices_count, _MIN_POOL)

    # No filters → whole library
    if not genres and not eras:
        return list(song_library)

    genres_set = set(genres) if genres else None
    eras_set   = set(eras)   if eras   else None

    def genre_ok(song: dict) -> bool:
        return genres_set is None or song["genre"] in genres_set

    def era_ok(song: dict) -> bool:
        return eras_set is None or song["era"] in eras_set

    # Step 1 — exact filter
    pool = [s for s in song_library if genre_ok(s) and era_ok(s)]
    if len(pool) >= min_needed:
        return pool

    # Step 2 — add related genres (era filter kept)
    if genres_set:
        related: set = set()
        for g in genres_set:
            related.update(related_genres_map.get(g, []))
        related -= genres_set  # avoid re-adding already-selected genres

        expanded = genres_set | related
        pool = [s for s in song_library
                if s["genre"] in expanded and era_ok(s)]
        if len(pool) >= min_needed:
            return pool

    # Step 3 — relax era, keep original genres
    if eras_set and genres_set:
        pool = [s for s in song_library if s["genre"] in genres_set]
        if len(pool) >= min_needed:
            return pool

    # Step 4 — full library
    return list(song_library)


# ── Distractor generation ──────────────────────────────────────────────────


def _generate_choices(
    correct_title: str,
    correct_artist: str,
    pool: List[Dict[str, str]],
    count: int = 4,
) -> List[dict]:
    """
    Build a multiple-choice list of `count` options from pool.
    Always includes the correct answer; the rest are random distractors.
    """
    distractors = [
        {"title": s["title"], "artist": s["artist"]}
        for s in pool
        if not (s["title"] == correct_title and s["artist"] == correct_artist)
    ]
    random.shuffle(distractors)

    n_wrong = min(count - 1, len(distractors))
    choices = distractors[:n_wrong]
    choices.append({"title": correct_title, "artist": correct_artist})
    random.shuffle(choices)
    return choices


# ── Service ────────────────────────────────────────────────────────────────


class iTunesService:
    """
    Stateless wrapper around the iTunes Search API. No auth needed.
    """

    def search_track(self, artist: str, title: str) -> Optional[TrackInfo]:
        """
        Search iTunes for (artist, title). Returns the best match with a
        valid previewUrl, or None if no suitable match exists.

        Matching strategy:
          1. Exact (fuzzy) title match among top 5 results — best signal.
          2. Fallback: first result with a previewUrl.
          3. None if no result has a previewUrl.
        """
        params = {
            "term":   f"{artist} {title}",
            "media":  "music",
            "entity": "song",
            "limit":  5,
        }
        try:
            resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
        except requests.RequestException as exc:
            raise iTunesFetchError(f"iTunes network error: {exc}") from exc

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise iTunesFetchError(f"iTunes error {resp.status_code}: {exc}") from exc

        results = resp.json().get("results", [])
        if not results:
            return None

        # Pass 1: exact fuzzy title match
        for item in results:
            if item.get("previewUrl") and _title_close(item.get("trackName", ""), title):
                info = _item_to_track_info(item, title, artist)
                if info:
                    return info

        # Pass 2: any result with a preview
        for item in results:
            if item.get("previewUrl"):
                info = _item_to_track_info(item, title, artist)
                if info:
                    return info

        return None

    def fetch_rounds(
        self,
        song_library: List[Dict[str, str]],
        count: int,
        choices_count: int = 4,
        clip_duration: int = 8,
        genres: Optional[List[str]] = None,
        eras: Optional[List[str]] = None,
        related_genres_map: Optional[Dict[str, List[str]]] = None,
    ) -> List[dict]:
        """
        Resolve `count` unique tracks from song_library via iTunes.

        genres / eras filter which songs are eligible. If the filtered pool
        is too small, _build_song_pool automatically widens the search.

        Returns round dicts:
            {
              title, artist,
              previewUrl,   ← played by <audio src=...> on the frontend
              duration,     ← seconds of the 30s preview to play
              thumbnail,    ← 300x300 iTunes artwork
              choices       ← multiple-choice options (list of {title, artist})
            }
        """
        if not song_library:
            raise iTunesFetchError("song_library is empty — nothing to search for.")

        pool = _build_song_pool(
            song_library,
            genres,
            eras,
            count,
            choices_count,
            related_genres_map or {},
        )

        if len(pool) < choices_count:
            raise iTunesFetchError(
                f"Song pool has only {len(pool)} songs but choices_count={choices_count}. "
                "Add more songs or reduce choices_count."
            )

        candidates = list(pool)
        random.shuffle(candidates)

        seen_previews: set = set()
        rounds: List[dict] = []

        for song in candidates:
            if len(rounds) >= count:
                break
            track = self.search_track(song["artist"], song["title"])
            if track is None or track.preview_url in seen_previews:
                continue
            seen_previews.add(track.preview_url)
            rounds.append({
                "title":      track.title,
                "artist":     track.artist,
                "previewUrl": track.preview_url,
                "duration":   clip_duration,
                "thumbnail":  track.artwork_url,
                "choices":    _generate_choices(
                    track.title, track.artist, pool, choices_count
                ),
            })

        if len(rounds) < count:
            raise iTunesFetchError(
                f"Could only find {len(rounds)} tracks on iTunes (needed {count}). "
                "Try selecting different genres/eras, or reduce the round count."
            )

        return rounds
