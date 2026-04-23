import React, { useEffect, useState } from 'react';
import './FeedbackBanner.css';

const AUTO_NEXT_MS = 3500;

/**
 * Displays round result after an answer is submitted.
 * Auto-advances after AUTO_NEXT_MS milliseconds; player can skip early.
 *
 * Props:
 *   result  – AnswerResult from POST /answer:
 *             { titleCorrect, artistCorrect, correctTitle, correctArtist,
 *               pointsEarned, totalScore, gameComplete, roundNumber }
 *   onNext  – callback to advance (fetch next round or go to results)
 */
export default function FeedbackBanner({ result, onNext }) {
  const {
    titleCorrect, artistCorrect,
    correctTitle, correctArtist,
    pointsEarned, totalScore,
    gameComplete,
  } = result;

  // Countdown displayed on the "Next" button.
  const [countdown, setCountdown] = useState(Math.round(AUTO_NEXT_MS / 1000));

  useEffect(() => {
    // Auto-advance timer.
    const advance = setTimeout(onNext, AUTO_NEXT_MS);

    // Decrement the button countdown every second.
    const tick = setInterval(() => {
      setCountdown((c) => Math.max(0, c - 1));
    }, 1000);

    return () => {
      clearTimeout(advance);
      clearInterval(tick);
    };
    // onNext is stable (useCallback in GameScreen).
  }, [onNext]);

  const bothCorrect = titleCorrect && artistCorrect;
  const partlyCorrect = titleCorrect || artistCorrect;
  const variant = bothCorrect ? 'correct' : partlyCorrect ? 'partial' : 'wrong';
  const icon = bothCorrect ? '🎉' : partlyCorrect ? '🤏' : '❌';

  return (
    <div className={`feedback-banner feedback-banner--${variant}`} role="status" aria-live="polite">

      {/* ── Result icon ─────────────────────────────────────────────────── */}
      <div className="feedback-icon">{icon}</div>

      {/* ── Correct answer reveal ────────────────────────────────────────── */}
      <div className="feedback-answer">
        <span className="feedback-title">{correctTitle}</span>
        <span className="feedback-artist">{correctArtist}</span>
      </div>

      {/* ── Per-field breakdown ──────────────────────────────────────────── */}
      <div className="feedback-fields">
        <span className={`feedback-field ${titleCorrect ? 'feedback-field--ok' : 'feedback-field--miss'}`}>
          {titleCorrect ? '✓' : '✗'} Titlu
        </span>
        <span className={`feedback-field ${artistCorrect ? 'feedback-field--ok' : 'feedback-field--miss'}`}>
          {artistCorrect ? '✓' : '✗'} Artist
        </span>
      </div>

      {/* ── Points earned this round ─────────────────────────────────────── */}
      <div className="feedback-points">
        <span className="points-earned">+{pointsEarned} pts</span>
        <span className="points-total">Total: {totalScore}</span>
      </div>

      {/* ── Manual advance button ────────────────────────────────────────── */}
      <button className="next-btn" onClick={onNext}>
        {gameComplete
          ? 'Rezultate finale →'
          : `Runda următoare → (${countdown}s)`}
      </button>
    </div>
  );
}
