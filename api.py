"""
api.py — Flask REST API for Guess the Song.

Audio source: iTunes Search API (replaced YouTube IFrame 2024-04).
Rationale: YouTube IFrame + Chrome autoplay policy produced ~40% audio
reliability on low-MEI origins. iTunes previewUrls play in a native
<audio> element with zero autoplay headaches.

Contract (v2):

  POST /api/game/new
    → 201  { sessionId, totalRounds, difficulty, mode, clipDuration, roundTimeout }
    → 400  invalid params
    → 502  iTunes unreachable

  GET  /api/game/<id>/round
    → 200  { roundNumber, totalRounds, previewUrl, duration, thumbnail, mode,
              choices? }   ← choices present only in multiple_choice mode
    → 200  { finished: true, totalRounds }   ← when all rounds answered
    → 404  session not found

  POST /api/game/<id>/answer
    MC mode  body: { "choiceIndex": 2 }
    FT mode  body: { "title": "...", "artist": "..." }
    → 200  { roundNumber, titleCorrect, artistCorrect, correctTitle, correctArtist,
              previewUrl, pointsEarned, totalScore, gameComplete }
    → 400  game complete / wrong mode / bad index
    → 404  session not found

  GET  /api/game/<id>/results
    → 200  { sessionId, totalScore, maxPossibleScore, totalRounds, rounds: [...] }
    → 404  session not found

  GET  /api/health
    → 200  { status: "ok" }
"""

import os

from flask import Flask, jsonify, request
from flask_cors import CORS

import game
from config import ERAS, GENRES, RELATED_GENRES, SONG_LIBRARY, GameConfig
from game import ChoiceIndexError, EmptyGuessError, WrongModeError
from itunes_service import iTunesFetchError, iTunesService

app = Flask(__name__)

# ── CORS ───────────────────────────────────────────────────────────────────
# This is a public game with no authentication or sensitive user data.
# We allow all origins ("*") so that any Vercel preview URL, local dev
# server, or future domain works without manual config changes.
# If auth is ever added, restrict this to specific origins.

CORS(
    app,
    resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"],
    }},
    supports_credentials=False,
)

_VALID_MODES = ("multiple_choice", "free_text")
_VALID_DIFFICULTIES = ("easy", "normal", "hard")


# ── Routes ─────────────────────────────────────────────────────────────────


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/game/new", methods=["POST"])
def new_game():
    """
    Body (JSON, all fields optional):
      {
        "rounds":     5,                  // integer 1-20, default 5
        "difficulty": "normal",           // "easy" | "normal" | "hard"
        "mode":       "multiple_choice"   // "multiple_choice" | "free_text"
      }
    """
    data = request.get_json(silent=True) or {}

    # ── Validate + parse inputs ────────────────────────────────────────────
    try:
        rounds = int(data.get("rounds", 5))
    except (TypeError, ValueError):
        return jsonify({"error": "'rounds' must be an integer between 1 and 20"}), 400

    difficulty = str(data.get("difficulty", "normal"))
    mode = str(data.get("mode", "multiple_choice"))

    # ── genres / eras (optional multi-select filters) ──────────────────────
    genres_raw = data.get("genres", [])
    eras_raw   = data.get("eras", [])

    if not isinstance(genres_raw, list):
        return jsonify({"error": "'genres' must be a list"}), 400
    if not isinstance(eras_raw, list):
        return jsonify({"error": "'eras' must be a list"}), 400

    invalid_genres = [g for g in genres_raw if g not in GENRES]
    invalid_eras   = [e for e in eras_raw   if e not in ERAS]
    if invalid_genres:
        return jsonify({"error": f"Invalid genres: {invalid_genres}. Valid: {GENRES}"}), 400
    if invalid_eras:
        return jsonify({"error": f"Invalid eras: {invalid_eras}. Valid: {ERAS}"}), 400

    # Empty list ⟹ no filter (all genres / all eras)
    genres = genres_raw or None
    eras   = eras_raw   or None

    if rounds < 1 or rounds > 20:
        return jsonify({"error": "'rounds' must be between 1 and 20"}), 400
    if difficulty not in _VALID_DIFFICULTIES:
        return jsonify({"error": f"'difficulty' must be one of: {', '.join(_VALID_DIFFICULTIES)}"}), 400
    if mode not in _VALID_MODES:
        return jsonify({"error": f"'mode' must be one of: {', '.join(_VALID_MODES)}"}), 400

    # ── Build config ───────────────────────────────────────────────────────
    config = GameConfig()
    config.apply_difficulty(difficulty)

    # ── Fetch rounds from iTunes ───────────────────────────────────────────
    try:
        service = iTunesService()
        round_data = service.fetch_rounds(
            SONG_LIBRARY,
            rounds,
            choices_count=config.choices_count,
            clip_duration=config.clip_duration_seconds,
            genres=genres,
            eras=eras,
            related_genres_map=RELATED_GENRES,
        )
    except iTunesFetchError as exc:
        return jsonify({"error": str(exc)}), 502

    # ── Create session ─────────────────────────────────────────────────────
    session = game.create_session(
        round_data,
        {
            "mode": mode,
            "totalRounds": rounds,
            "difficulty": difficulty,
            "partialMatch": config.partial_match_enabled,
            "partialMatchThreshold": config.partial_match_threshold,
            "pointsTitle": config.points_correct_title,
            "pointsArtist": config.points_correct_artist,
        },
    )

    return jsonify({
        "sessionId": session.session_id,
        "totalRounds": rounds,
        "difficulty": difficulty,
        "mode": mode,
        "clipDuration": config.clip_duration_seconds,
        "roundTimeout": config.round_timeout_seconds,
    }), 201


@app.route("/api/game/<session_id>/round", methods=["GET"])
def get_round(session_id: str):
    """
    Returns current round data. title/artist are never included here.

    multiple_choice response includes:
      "choices": [ { "title": "...", "artist": "..." }, ... ]

    When the game is finished:
      { "finished": true, "totalRounds": N }
    """
    session = game.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.is_complete:
        return jsonify({"finished": True, "totalRounds": len(session.rounds)})

    round_data = session.get_current_round_data()
    if round_data is None:
        return jsonify({"finished": True, "totalRounds": len(session.rounds)})
    return jsonify(round_data)


@app.route("/api/game/<session_id>/answer", methods=["POST"])
def submit_answer(session_id: str):
    """
    multiple_choice mode body:
      { "choiceIndex": 2 }          ← 0-based index into choices array

    free_text mode body:
      { "title": "Shape of You", "artist": "Ed Sheeran" }

    artist is optional in free_text mode (title-only guesses earn 100 pts, no bonus).
    """
    session = game.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.is_complete:
        return jsonify({"error": "Game is already complete. Fetch /results."}), 400

    data = request.get_json(silent=True) or {}
    title_guess = str(data.get("title", "")).strip()
    artist_guess = str(data.get("artist", "")).strip()

    raw_index = data.get("choiceIndex", -1)
    try:
        choice_index = int(raw_index)
    except (TypeError, ValueError):
        choice_index = -1

    try:
        result = session.submit_answer(title_guess, artist_guess, choice_index)
    except ChoiceIndexError as exc:
        return jsonify({"error": str(exc)}), 400
    except WrongModeError as exc:
        return jsonify({"error": str(exc)}), 400
    except EmptyGuessError as exc:
        return jsonify({"error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    result["gameComplete"] = session.is_complete
    return jsonify(result)


@app.route("/api/game/<session_id>/results", methods=["GET"])
def get_results(session_id: str):
    """
    Available at any point during the game (not only after completion).
    rounds[] contains only answered rounds.
    """
    session = game.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(session.get_final_results())
