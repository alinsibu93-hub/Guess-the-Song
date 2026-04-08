# 🎵 Guess the Song

A terminal-based music quiz game powered by the **Spotify Web API**.
Listen to a short audio clip and guess the song title — before the timer runs out!

---

## How It Works

1. The game fetches real songs from Spotify (using popular artists as a source).
2. A **short audio preview** (3–15 seconds depending on difficulty) plays automatically.
3. You type your guess while a **live countdown timer** ticks.
4. Get points for the correct title — and a bonus for naming the artist too.
5. After all rounds, a final scoreboard shows your total score and performance.

---

## Features

- Real-time countdown timer per round
- 3 difficulty modes: Easy / Normal / Hard
- Artist bonus scoring
- Partial match support (typos are forgiven on Easy/Normal)
- Instant feedback after each guess
- Pre-fetches all tracks before the game starts (no mid-game pauses)
- Fully offline mock mode for testing without a network connection

---

## Requirements

- Python 3.10+
- A free [Spotify Developer account](https://developer.spotify.com/dashboard) (no Premium needed)
- `pygame` for audio playback

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/alinsibu93-hub/Guess-the-Song.git
cd Guess-the-Song
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Spotify credentials

Copy the example env file and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here
```

Get your credentials at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) — create a free app, copy the Client ID and Client Secret.

### 4. Run the game
```bash
python main.py
```

Optional flags:
```bash
python main.py --difficulty hard --rounds 3
python main.py --no-artist        # skip artist bonus round
python main.py --verbose          # show debug logs
```

### 5. Offline / mock mode (no Spotify needed)
```bash
python mock_spotify.py
```

---

## Project Structure

```
guess_the_song/
├── main.py              # Entry point and CLI argument handling
├── config.py            # All game settings in one place
├── spotify_service.py   # Spotify API integration (artist search + top tracks)
├── audio_player.py      # Cross-platform audio playback (pygame)
├── game_timer.py        # Non-blocking countdown timer
├── game_engine.py       # Core game loop and scoring logic
├── ui.py                # Terminal output, colors, and prompts
├── mock_spotify.py      # Offline demo mode
├── requirements.txt     # Python dependencies
├── .env.example         # Credential template (safe to commit)
└── tests/               # Unit tests (pytest)
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests cover: guess matching logic, timer behavior, and Spotify service (fully mocked — no credentials needed).

---

## Scoring

| Event | Points |
|---|---|
| Correct song title | +100 |
| Correct artist (bonus) | +50 |
| Timeout or wrong answer | 0 |

---

## Difficulty Modes

| Mode | Clip length | Timer |
|---|---|---|
| Easy | 15 seconds | 20 seconds |
| Normal | 8 seconds | 10 seconds |
| Hard | 3 seconds | 7 seconds |

---

## License

MIT — free to use, modify, and distribute.
