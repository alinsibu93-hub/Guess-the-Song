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
from typing import List, Optional, Tuple

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


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


# ── Service ────────────────────────────────────────────────────────────────


class iTunesService:
    """
    Stateless wrapper around the iTunes Search API. No auth needed, so
    there's no api_key argument — constructor is a no-op for symmetry
    with the previous YouTubeService.
    """

    def search_track(self, artist: str, title: str) -> Optional[TrackInfo]:
        """
        Search iTunes for (artist, title). Returns the best match with a
        valid previewUrl, or None if no suitable match exists.

        Matching strategy:
          1. Exact (fuzzy) title match among top 5 results — best signal.
          2. Fallback: first result with a previewUrl (sometimes Apple's
             relevance ranking beats title matching).
          3. None if no result has a previewUrl (rare — some obscure or
             region-restricted tracks lack previews).
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
        song_library: List[Tuple[str, str]],
        count: int,
        choices_count: int = 4,
        clip_duration: int = 8,
    ) -> List[dict]:
        """
        Resolve `count` unique (artist, title) pairs from song_library via iTunes.

        Returns round dicts with the same shape the game engine expects,
        except the "videoId"/"startTime" pair is replaced by "previewUrl":

            {
              title, artist,
              previewUrl,   ← played by <audio src=...> on the frontend
              duration,     ← how many seconds of the 30s preview to play
              thumbnail,    ← 300x300 iTunes artwork
              choices       ← multiple-choice options
            }

        Since iTunes previews are pre-selected to be the chorus / most
        recognisable section, we play from second 0 of the preview — no
        random startTime needed (and no chance of landing on silence).
        """
        if not song_library:
            raise iTunesFetchError("song_library is empty — nothing to search for.")
        if len(song_library) < choices_count:
            raise iTunesFetchError(
                f"song_library has {len(song_library)} songs but choices_count={choices_count} "
                f"requires at least {choices_count}. Add more songs or reduce choices_count."
            )

        candidates = list(song_library)
        random.shuffle(candidates)

        seen_previews: set = set()
        rounds: List[dict] = []

        for artist, title in candidates:
            if len(rounds) >= count:
                break
            track = self.search_track(artist, title)
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
                    track.title, track.artist, song_library, choices_count
                ),
            })

        if len(rounds) < count:
            raise iTunesFetchError(
                f"Could only find {len(rounds)} tracks on iTunes, needed {count}. "
                "Add more songs to the library or reduce the round count."
            )

        return rounds


# ── Distractor generation (unchanged from youtube_service) ─────────────────


def _generate_choices(
    correct_title: str,
    correct_artist: str,
    song_library: List[Tuple[str, str]],
    count: int = 4,
) -> List[dict]:
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
