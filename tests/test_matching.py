"""
tests/test_matching.py — Unit tests for guess-matching logic.

Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import _title_matches, _artist_matches, _normalize


class TestNormalize:
    def test_strips_case(self):
        assert _normalize("Hello World") == "hello world"

    def test_strips_punctuation(self):
        assert _normalize("  Song Title!  ") == "song title"

    def test_empty(self):
        assert _normalize("") == ""


class TestTitleMatches:
    def test_exact(self):
        assert _title_matches("Bohemian Rhapsody", "Bohemian Rhapsody", False, 0.6)

    def test_case_insensitive(self):
        assert _title_matches("bohemian rhapsody", "Bohemian Rhapsody", False, 0.6)

    def test_no_match(self):
        assert not _title_matches("Yellow Submarine", "Bohemian Rhapsody", False, 0.6)

    def test_partial_match_above_threshold(self):
        assert _title_matches("Bohemian Rapsody", "Bohemian Rhapsody", True, 0.6)

    def test_partial_match_below_threshold(self):
        assert not _title_matches("xyz", "Bohemian Rhapsody", True, 0.9)

    def test_partial_disabled(self):
        assert not _title_matches("Bohemian Rapsody", "Bohemian Rhapsody", False, 0.6)

    def test_empty_guess(self):
        assert not _title_matches("", "Bohemian Rhapsody", True, 0.6)


class TestArtistMatches:
    def test_exact(self):
        assert _artist_matches("Queen", "Queen")

    def test_first_name_only(self):
        assert _artist_matches("Taylor", "Taylor Swift")

    def test_different_artist(self):
        assert not _artist_matches("Adele", "Queen")

    def test_empty_guess(self):
        assert not _artist_matches("", "Queen")

    def test_case_insensitive(self):
        assert _artist_matches("taylor swift", "Taylor Swift")
