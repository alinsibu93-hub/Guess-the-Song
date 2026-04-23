import React, { useState, useEffect } from 'react';
import MultipleChoice from './MultipleChoice';
import './GuessInput.css';

/**
 * Unified input component for both game modes.
 * Renders MultipleChoice cards or a free-text form based on `mode`.
 *
 * Props:
 *   mode       – 'multiple_choice' | 'free_text'
 *   choices    – (MC only) array of { title, artist } from GET /round
 *   onSubmit   – callback({ choiceIndex } | { title, artist? })
 *   disabled   – disables all inputs (SUBMITTING state in GameScreen)
 *   difficulty – shown as a hint in hard free_text mode
 */
export default function GuessInput({ mode, choices, onSubmit, disabled, difficulty }) {
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  // Tracks clicked choice to disable cards immediately after selection.
  const [selectedChoice, setSelectedChoice] = useState(null);

  // Reset local state when a new round begins.
  // The `disabled` prop flips false→true→false between rounds;
  // we reset on the false→true transition (start of SUBMITTING/FEEDBACK)
  // actually cleaner to reset when round data changes — done via key in GameScreen.
  useEffect(() => {
    setTitle('');
    setArtist('');
    setSelectedChoice(null);
  }, [mode]); // also reset if mode somehow changes (shouldn't, but defensive)

  // ── Multiple choice ────────────────────────────────────────────────────
  if (mode === 'multiple_choice') {
    function handleSelect(index) {
      if (disabled || selectedChoice !== null) return;
      setSelectedChoice(index);
      // Auto-submit — no separate button needed for MC mode.
      onSubmit({ choiceIndex: index });
    }

    return (
      <MultipleChoice
        choices={choices ?? []}
        onSelect={handleSelect}
        disabled={disabled}
        selected={selectedChoice}
      />
    );
  }

  // ── Free text ──────────────────────────────────────────────────────────
  function handleSubmit(e) {
    e.preventDefault();
    // Guard: title is required; disabled catches SUBMITTING state.
    if (disabled || !title.trim()) return;
    onSubmit({ title: title.trim(), artist: artist.trim() });
  }

  return (
    <form className={`free-text-form${title.trim() ? ' free-text-form--ready' : ''}`} onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label htmlFor="ft-title">Titlu piesă *</label>
        <input
          id="ft-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="ex: Shape of You"
          disabled={disabled}
          autoComplete="off"
          // Focus the title field as soon as the guess area appears.
          autoFocus
        />
      </div>

      <div className="field">
        <label htmlFor="ft-artist">
          Artist
          <span className="bonus-hint"> +50 pts</span>
        </label>
        <input
          id="ft-artist"
          type="text"
          value={artist}
          onChange={(e) => setArtist(e.target.value)}
          placeholder="ex: Ed Sheeran  (opțional)"
          disabled={disabled}
          autoComplete="off"
          // Allow pressing Enter in the artist field to submit.
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(e); }}
        />
      </div>

      {/* Hard mode warning — partial matching is disabled server-side. */}
      {difficulty === 'hard' && (
        <p className="hard-hint">
          ⚠️ Hard: potrivire exactă — fără aproximare.
        </p>
      )}

      <button
        type="submit"
        className="submit-btn"
        disabled={disabled || !title.trim()}
      >
        {disabled ? 'Se verifică…' : 'Trimite ▶'}
      </button>
    </form>
  );
}
