import React, { useState } from 'react';
import { startGame } from '../api/gameApi';
import './StartScreen.css';

// Loading messages shown progressively as POST /new takes time.
const LOADING_MESSAGES = [
  'Se pregătesc piesele…',
  'Se caută pe iTunes…',
  'Aproape gata…',
  'Durează mai mult ca de obicei…',
];

const GENRE_OPTIONS = [
  { key: 'pop',        label: 'Pop'        },
  { key: 'rock',       label: 'Rock'       },
  { key: 'hiphop',     label: 'Hip-Hop'    },
  { key: 'rb',         label: 'R&B'        },
  { key: 'electronic', label: 'Electronic' },
  { key: 'metal',      label: 'Metal'      },
  { key: 'indie',      label: 'Indie'      },
  { key: 'latin',      label: 'Latin'      },
  { key: 'kpop',       label: 'K-Pop'      },
];

const ERA_OPTIONS = [
  { key: '80s',   label: '80s'   },
  { key: '90s',   label: '90s'   },
  { key: '2000s', label: '2000s' },
  { key: '2010s', label: '2010s' },
  { key: '2020s', label: '2020s' },
];

/**
 * Game configuration form. Calls POST /api/game/new on submit.
 *
 * Props:
 *   onStart(session) – called with session data when the backend responds.
 */
export default function StartScreen({ onStart }) {
  const [config, setConfig] = useState({
    rounds:     5,
    difficulty: 'normal',
    mode:       'multiple_choice',
    genres:     [],
    eras:       [],
  });
  const [loading,  setLoading]  = useState(false);
  const [msgIndex, setMsgIndex] = useState(0);
  const [error,    setError]    = useState(null);

  function toggleGenre(key) {
    setConfig(c => ({
      ...c,
      genres: c.genres.includes(key)
        ? c.genres.filter(g => g !== key)
        : [...c.genres, key],
    }));
  }

  function toggleEra(key) {
    setConfig(c => ({
      ...c,
      eras: c.eras.includes(key)
        ? c.eras.filter(e => e !== key)
        : [...c.eras, key],
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);
    setMsgIndex(0);

    // Escalate loading message every 4 seconds so the user knows we're working.
    const timers = [4000, 8000, 14000].map((delay, i) =>
      setTimeout(() => setMsgIndex(i + 1), delay)
    );

    try {
      const session = await startGame(config);
      onStart(session);
    } catch (err) {
      setError(friendlyError(err));
      setLoading(false);
    } finally {
      timers.forEach(clearTimeout);
    }
  }

  function friendlyError(err) {
    if (err.status === 502) return 'Nu am putut contacta iTunes. Verifică conexiunea.';
    if (err.body?.error)    return err.body.error;
    return 'A apărut o eroare. Încearcă din nou.';
  }

  if (loading) {
    return (
      <div className="start-screen start-screen--loading">
        <h1>🎵 Guess the Song</h1>
        <div className="spinner" />
        <p className="loading-msg">{LOADING_MESSAGES[Math.min(msgIndex, LOADING_MESSAGES.length - 1)]}</p>
        {msgIndex >= 3 && (
          <button className="cancel-btn" onClick={() => setLoading(false)}>
            Anulează
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="start-screen">
      <h1>🎵 Guess the Song</h1>
      <p className="subtitle">Ghicește piesa după un clip audio scurt.</p>

      <form className="start-form" onSubmit={handleSubmit}>

        {/* ── Rounds ──────────────────────────────────────────────────── */}
        <div className="field">
          <label htmlFor="rounds-select">Număr de runde</label>
          <select
            id="rounds-select"
            value={config.rounds}
            onChange={(e) => setConfig({ ...config, rounds: Number(e.target.value) })}
          >
            {[3, 5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>{n} runde</option>
            ))}
          </select>
        </div>

        {/* ── Difficulty ──────────────────────────────────────────────── */}
        <fieldset className="field">
          <legend>Dificultate</legend>
          {[
            { value: 'easy',   label: '😌 Ușor',   hint: '15s clip, potrivire parțială' },
            { value: 'normal', label: '😐 Normal',  hint: '8s clip' },
            { value: 'hard',   label: '😈 Hard',    hint: '3s clip, potrivire exactă' },
          ].map(({ value, label, hint }) => (
            <label key={value} className="radio-label">
              <input
                type="radio"
                name="difficulty"
                value={value}
                checked={config.difficulty === value}
                onChange={() => setConfig({ ...config, difficulty: value })}
              />
              <span className="radio-text">
                {label}
                <small className="radio-hint">{hint}</small>
              </span>
            </label>
          ))}
        </fieldset>

        {/* ── Mode ────────────────────────────────────────────────────── */}
        <fieldset className="field">
          <legend>Mod de joc</legend>
          {[
            { value: 'multiple_choice', label: '🔠 Răspuns multiplu', hint: 'Alege din 4 opțiuni' },
            { value: 'free_text',       label: '✍️ Text liber',       hint: 'Scrie titlul și artistul' },
          ].map(({ value, label, hint }) => (
            <label key={value} className="radio-label">
              <input
                type="radio"
                name="mode"
                value={value}
                checked={config.mode === value}
                onChange={() => setConfig({ ...config, mode: value })}
              />
              <span className="radio-text">
                {label}
                <small className="radio-hint">{hint}</small>
              </span>
            </label>
          ))}
        </fieldset>

        {/* ── Genres ──────────────────────────────────────────────────── */}
        <fieldset className="field">
          <legend>
            Genuri
            <span className="filter-hint">(opțional — implicit: toate)</span>
          </legend>
          <div className="toggle-group">
            {GENRE_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                className={`toggle-btn${config.genres.includes(key) ? ' toggle-btn--on' : ''}`}
                onClick={() => toggleGenre(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </fieldset>

        {/* ── Eras ────────────────────────────────────────────────────── */}
        <fieldset className="field">
          <legend>
            Epoci
            <span className="filter-hint">(opțional — implicit: toate)</span>
          </legend>
          <div className="toggle-group">
            {ERA_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                className={`toggle-btn${config.eras.includes(key) ? ' toggle-btn--on' : ''}`}
                onClick={() => toggleEra(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </fieldset>

        {error && <p className="form-error" role="alert">⚠️ {error}</p>}

        <button type="submit" className="start-btn">
          Începe jocul →
        </button>
      </form>
    </div>
  );
}
