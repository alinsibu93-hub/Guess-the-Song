"""
tests/test_game_session.py — Unit tests for GameSession (both modes).

Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import GameSession, ChoiceIndexError, WrongModeError, _normalize


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _mc_session(score_pts=(100, 50)) -> GameSession:
    rounds = [
        {
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "videoId": "vid1",
            "startTime": 45,
            "duration": 7,
            "thumbnail": None,
            "choices": [
                {"title": "Shape of You", "artist": "Ed Sheeran"},  # index 0 — correct
                {"title": "Yellow", "artist": "Coldplay"},
                {"title": "Hello", "artist": "Adele"},
                {"title": "Believer", "artist": "Imagine Dragons"},
            ],
        },
        {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "videoId": "vid2",
            "startTime": 60,
            "duration": 5,
            "thumbnail": None,
            "choices": [
                {"title": "Blinding Lights", "artist": "The Weeknd"},  # index 0 — correct
                {"title": "Radioactive", "artist": "Imagine Dragons"},
                {"title": "Anti-Hero", "artist": "Taylor Swift"},
                {"title": "Lose Yourself", "artist": "Eminem"},
            ],
        },
    ]
    config = {
        "mode": "multiple_choice",
        "partialMatch": True,
        "partialMatchThreshold": 0.6,
        "pointsTitle": score_pts[0],
        "pointsArtist": score_pts[1],
    }
    return GameSession(rounds, config)


def _ft_session() -> GameSession:
    rounds = [
        {
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "videoId": "vid3",
            "startTime": 30,
            "duration": 8,
            "thumbnail": None,
            "choices": [],
        }
    ]
    config = {
        "mode": "free_text",
        "partialMatch": True,
        "partialMatchThreshold": 0.6,
        "pointsTitle": 100,
        "pointsArtist": 50,
    }
    return GameSession(rounds, config)


# ── Session basics ────────────────────────────────────────────────────────────


class TestSessionBasics:
    def test_session_id_is_unique(self):
        s1, s2 = _mc_session(), _mc_session()
        assert s1.session_id != s2.session_id

    def test_starts_at_round_zero(self):
        s = _mc_session()
        assert s.current_round == 0
        assert not s.is_complete

    def test_complete_after_all_rounds(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)
        s.submit_answer(choice_index=0)
        assert s.is_complete

    def test_raises_on_submit_after_complete(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)
        s.submit_answer(choice_index=0)
        try:
            s.submit_answer(choice_index=0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# ── get_current_round_data ────────────────────────────────────────────────────


class TestGetRoundData:
    def test_mc_round_includes_choices(self):
        s = _mc_session()
        data = s.get_current_round_data()
        assert "choices" in data
        assert len(data["choices"]) == 4

    def test_ft_round_excludes_choices(self):
        s = _ft_session()
        data = s.get_current_round_data()
        assert "choices" not in data

    def test_round_data_has_required_fields(self):
        s = _mc_session()
        data = s.get_current_round_data()
        for field in ("roundNumber", "totalRounds", "videoId", "startTime", "duration", "mode"):
            assert field in data, f"Missing: {field}"

    def test_title_and_artist_not_in_round_data(self):
        s = _mc_session()
        data = s.get_current_round_data()
        assert "title" not in data
        assert "artist" not in data

    def test_returns_none_when_complete(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)
        s.submit_answer(choice_index=0)
        assert s.get_current_round_data() is None

    def test_round_number_increments(self):
        s = _mc_session()
        assert s.get_current_round_data()["roundNumber"] == 1
        s.submit_answer(choice_index=0)
        assert s.get_current_round_data()["roundNumber"] == 2


# ── Multiple choice submit ────────────────────────────────────────────────────


class TestMultipleChoiceSubmit:
    def test_correct_choice_gives_full_points(self):
        s = _mc_session()
        result = s.submit_answer(choice_index=0)  # index 0 is correct
        assert result["titleCorrect"] is True
        assert result["artistCorrect"] is True
        assert result["pointsEarned"] == 150  # 100 + 50

    def test_wrong_choice_gives_zero_points(self):
        s = _mc_session()
        result = s.submit_answer(choice_index=1)  # index 1 is wrong
        assert result["titleCorrect"] is False
        assert result["artistCorrect"] is False
        assert result["pointsEarned"] == 0

    def test_result_reveals_correct_title_and_artist(self):
        s = _mc_session()
        result = s.submit_answer(choice_index=1)
        assert result["correctTitle"] == "Shape of You"
        assert result["correctArtist"] == "Ed Sheeran"

    def test_result_includes_video_id(self):
        s = _mc_session()
        result = s.submit_answer(choice_index=0)
        assert result["videoId"] == "vid1"

    def test_score_accumulates(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)  # 150 pts
        result = s.submit_answer(choice_index=0)  # 150 pts
        assert result["totalScore"] == 300

    def test_invalid_choice_index_raises(self):
        s = _mc_session()
        try:
            s.submit_answer(choice_index=99)
            assert False, "Should have raised ChoiceIndexError"
        except ChoiceIndexError:
            pass

    def test_missing_choice_index_in_mc_mode_raises(self):
        s = _mc_session()
        try:
            s.submit_answer(title_guess="Shape of You")  # choice_index defaults to -1
            assert False, "Should have raised WrongModeError"
        except WrongModeError:
            pass

    def test_game_complete_flag(self):
        s = _mc_session()
        r1 = s.submit_answer(choice_index=0)
        assert r1.get("roundNumber") == 1
        r2 = s.submit_answer(choice_index=0)
        assert r2.get("roundNumber") == 2
        assert s.is_complete


# ── Free-text submit ──────────────────────────────────────────────────────────


class TestFreeTextSubmit:
    def test_exact_title_match(self):
        s = _ft_session()
        result = s.submit_answer(title_guess="Bohemian Rhapsody", artist_guess="Queen")
        assert result["titleCorrect"] is True
        assert result["artistCorrect"] is True
        assert result["pointsEarned"] == 150

    def test_partial_title_match(self):
        s = _ft_session()
        result = s.submit_answer(title_guess="Bohemian Rapsody")  # typo
        assert result["titleCorrect"] is True

    def test_artist_only_first_name(self):
        s = _ft_session()
        result = s.submit_answer(title_guess="Bohemian Rhapsody", artist_guess="Queen")
        assert result["artistCorrect"] is True

    def test_empty_title_raises(self):
        import pytest
        from game import EmptyGuessError
        s = _ft_session()
        with pytest.raises(EmptyGuessError):
            s.submit_answer(title_guess="", artist_guess="")

    def test_title_only_earns_title_points(self):
        s = _ft_session()
        result = s.submit_answer(title_guess="Bohemian Rhapsody", artist_guess="")
        assert result["titleCorrect"] is True
        assert result["artistCorrect"] is False
        assert result["pointsEarned"] == 100

    def test_choice_index_in_free_text_mode_raises(self):
        s = _ft_session()
        try:
            s.submit_answer(choice_index=0)
            assert False, "Should have raised WrongModeError"
        except WrongModeError:
            pass


# ── get_final_results ─────────────────────────────────────────────────────────


class TestFinalResults:
    def test_max_possible_score_correct(self):
        s = _mc_session()
        results = s.get_final_results()
        assert results["maxPossibleScore"] == 2 * 150  # 2 rounds × (100+50)

    def test_results_length_matches_answered_rounds(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)
        results = s.get_final_results()
        assert len(results["rounds"]) == 1

    def test_session_id_in_results(self):
        s = _mc_session()
        results = s.get_final_results()
        assert results["sessionId"] == s.session_id

    def test_total_score_in_results(self):
        s = _mc_session()
        s.submit_answer(choice_index=0)  # correct → 150
        s.submit_answer(choice_index=1)  # wrong  → 0
        results = s.get_final_results()
        assert results["totalScore"] == 150
