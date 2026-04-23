import React from 'react';
import './ProgressIndicator.css';

/**
 * Shows round position and current score.
 * The progress bar fills proportionally to answered rounds.
 *
 * Props:
 *   currentRound – 1-based index of the round being played
 *   totalRounds  – total rounds in this session
 *   score        – cumulative score so far
 */
export default function ProgressIndicator({ currentRound, totalRounds, score }) {
  // Progress reflects completed rounds (currentRound - 1), not the active one.
  const pct = totalRounds > 0 ? ((currentRound - 1) / totalRounds) * 100 : 0;

  return (
    <div className="progress-indicator">
      <div className="progress-meta">
        <span className="progress-round">
          Runda <strong>{currentRound}</strong> / {totalRounds}
        </span>
        <span className="progress-score">
          <strong>{score}</strong> pts
        </span>
      </div>

      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={currentRound - 1}
        aria-valuemin={0}
        aria-valuemax={totalRounds}
        aria-label={`Runda ${currentRound} din ${totalRounds}`}
      >
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
