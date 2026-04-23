import React, { useState } from 'react';
import { startGame } from '../api/gameApi';
import './StartScreen.css';

// Loading messages shown progressively as POST /new takes time.
const LOADING_MESSAGES = [
  'Se pregătesc piesele…',
  'Se caută pe YouTube…',
  'Aproape gata…',
  'Durează mai mult ca de obicei…',
];

/**
 * Game configuration form. Calls POST /api/game/new on submit.
 *
 * Props:
 *   onStart(session) – called with session data when the backend responds.
 */
export default function StartScreen({ onStart }) {
  const [config, setConfig] = useState({
    rounds: 5,
    difficulty: 'normal',
    mode: 'multiple_choice',
  });
  const [loading, setLoading] = useState(false);
  const [msgIndex, setMsgIndex] = useState(0);
  const [error, setError] = useState(null);

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
    if (err.status === 401) return 'Cheia API YouTube lipsește sau este invalidă.';
    if (err.status === 429) return 'Cota YouTube a fost depășită. Încearcă mâine.';
    if (err.status === 502) return 'Nu am putut contacta YouTube. Verifică conexiunea.';
    return 'A apărut o eroare. Încearcă din nou.';
  }

  if (loading) {
    return (
      <div className="start-screen start-screen--loading">
        <h1>🎵 Guess the Song</h1>
        <div className="spinner" />
        <p className="loading-msg">{LOADING_MESSAGES[Math.min(msgIndex, LOADING_MESSAGES.length - 1)]}</p>
        {/* Allow cancel only after a long wait — avoids confusing quick users. */}
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

        {error && <p className="form-error" role="alert">⚠️ {error}</p>}

        <button type="submit" className="start-btn">
          Începe jocul →
        </button>
      </form>
    </div>
  );
}
