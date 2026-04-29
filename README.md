# 🎵 Guess the Song

A web-based music quiz game — listen to a short audio clip and guess the song before time runs out.

---

## How It Works

1. Configure your game — rounds, difficulty, game mode, genres, and eras
2. Click **▶ Ascultă** to start the clip (3 / 8 / 15 seconds depending on difficulty)
3. A spinning vinyl disc animates while the audio plays and a countdown ticks
4. Guess by selecting one of 4 options (Multiple Choice) or typing freely (Free Text)
5. Instant feedback after each round — points for title + artist bonus
6. Final scoreboard with round-by-round breakdown

---

## Features

| | |
|---|---|
| 🎶 **303 curated songs** | 9 genres × 5 eras, all with iTunes previews |
| 🎛 **Genre & era filtering** | Multi-select toggles; narrow combos auto-fallback to related genres |
| 🎚 **3 difficulty levels** | Easy (15s) / Normal (8s) / Hard (3s) |
| 🔠 **2 game modes** | Multiple Choice (4 options) or Free Text (with partial match on Easy/Normal) |
| ⏱ **Round timer** | Auto-advances when time expires |
| 💿 **Vinyl disc visual** | Pure-CSS animated disc during playback — no song spoilers |
| 🔊 **~99% audio reliability** | HTML5 `<audio>` with iTunes `.m4a` previews — no iframe/autoplay issues |
| 📊 **Detailed results** | Per-round breakdown with correct answers and points |

---

## Song Library

303 tracks across 9 genres and 5 eras:

| Genre | 80s | 90s | 2000s | 2010s | 2020s | Total |
|---|---|---|---|---|---|---|
| Pop | 10 | 10 | 10 | 10 | 8 | **48** |
| Rock | 8 | 10 | 8 | 6 | 4 | **36** |
| Hip-Hop | 4 | 10 | 10 | 10 | 8 | **42** |
| R&B | 6 | 8 | 8 | 8 | 6 | **36** |
| Electronic | 6 | 6 | 8 | 8 | 6 | **34** |
| Metal | 6 | 8 | 6 | 4 | 2 | **26** |
| Indie | 4 | 6 | 6 | 8 | 6 | **30** |
| Latin | 2 | 4 | 6 | 8 | 8 | **28** |
| K-Pop | 0 | 2 | 4 | 9 | 8 | **23** |

When a genre+era combination has fewer songs than needed, the backend automatically widens the pool — first to related genres, then relaxes the era filter, then falls back to the full library.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, CSS custom properties (dark theme) |
| **Backend** | Python 3, Flask, Flask-CORS |
| **Audio source** | [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/) — public, no auth, 30s `.m4a` previews |
| **Frontend hosting** | [Vercel](https://vercel.com) |
| **Backend hosting** | [Render](https://render.com) (free tier, auto-deploy from GitHub) |

---

## REST API

```
POST /api/game/new
  Body: { rounds, difficulty, mode, genres[], eras[] }
  → 201 { sessionId, totalRounds, difficulty, mode, clipDuration, roundTimeout }

GET  /api/game/<id>/round
  → 200 { roundNumber, previewUrl, duration, thumbnail, mode, choices? }
  → 200 { finished: true, totalRounds }

POST /api/game/<id>/answer
  MC:   { "choiceIndex": 2 }
  FT:   { "title": "...", "artist": "..." }
  → 200 { roundNumber, titleCorrect, artistCorrect, correctTitle, correctArtist,
           previewUrl, pointsEarned, totalScore, gameComplete }

GET  /api/game/<id>/results
  → 200 { sessionId, totalScore, maxPossibleScore, totalRounds, rounds[] }

GET  /api/health
  → 200 { status: "ok" }
```

Full contract in [`swagger.yaml`](./swagger.yaml).

---

## Scoring

| Event | Points |
|---|---|
| Correct song title | +100 |
| Correct artist (bonus) | +50 |
| Timeout or wrong answer | 0 |

Partial match is enabled on Easy and Normal difficulty (tolerates typos).

---

## Project Structure

```
guess_the_song/
├── api.py               # Flask REST API — all game endpoints
├── game.py              # Session management and scoring logic
├── config.py            # 303-song SONG_LIBRARY, GENRES, ERAS, RELATED_GENRES,
│                        #   GameConfig (difficulty settings)
├── itunes_service.py    # iTunes Search API client + song pool filtering
├── requirements.txt     # Python dependencies
├── swagger.yaml         # OpenAPI spec for the REST API
├── tests/
│   ├── test_game_session.py
│   └── test_matching.py
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── vercel.json       # SPA rewrite rules + CSP headers
    └── src/
        ├── api/
        │   └── gameApi.js          # Typed wrappers for all API calls
        └── components/
            ├── StartScreen.jsx     # Config form with genre/era toggles
            ├── GameScreen.jsx      # Main game loop + state machine
            ├── PlayerOverlay.jsx   # HTML5 audio player + vinyl disc
            ├── AnswerSection.jsx   # Multiple choice / free text input
            └── ResultsScreen.jsx   # Final scoreboard
```

---

## Local Development

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask dev server (port 5000)
python api.py
```

No API keys or `.env` needed — iTunes Search API is public and unauthenticated.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server (port 5173, proxies /api/* → localhost:5000)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Running Tests

```bash
python -m pytest tests/ -v
```

---

## Deployment

| Service | Config |
|---|---|
| **Render** | Auto-deploys `main` branch; start command: `gunicorn api:app` |
| **Vercel** | Root directory set to `frontend`; build command: `npm run build` |

CORS is set to `*` — the game has no authentication or sensitive user data, so any origin is safe to allow. This also means Vercel preview URLs work without any manual configuration.

---

## License

MIT — free to use, modify, and distribute.
