import React from 'react';
import './ResultsScreen.css';

/**
 * Final scoreboard after all rounds are answered.
 *
 * Props:
 *   results   – { sessionId, totalScore, maxPossibleScore, totalRounds, rounds: [] }
 *   onNewGame – returns to StartScreen
 */
export default function ResultsScreen({ results, onNewGame }) {
  const { totalScore, maxPossibleScore, totalRounds, rounds } = results;
  const pct = maxPossibleScore > 0 ? Math.round((totalScore / maxPossibleScore) * 100) : 0;

  function medal() {
    if (pct >= 90) return '🥇';
    if (pct >= 60) return '🥈';
    if (pct >= 30) return '🥉';
    return '🎵';
  }

  function verdict() {
    if (pct >= 90) return 'Impresionant! Ești un adevărat meloman.';
    if (pct >= 60) return 'Bine jucat! Mai ai de lucru.';
    if (pct >= 30) return 'Nu e rău pentru început.';
    return 'Mai multă muzică, mai puțin Netflix. 😄';
  }

  return (
    <div className="results-screen">
      <div className="results-header">
        <span className="results-medal">{medal()}</span>
        <h1>Rezultate finale</h1>
        <p className="results-verdict">{verdict()}</p>
      </div>

      {/* ── Score summary ──────────────────────────────────────────────── */}
      <div className="results-summary">
        <div className="score-display">
          <span className="score-value">{totalScore}</span>
          <span className="score-max">/ {maxPossibleScore} pts</span>
        </div>
        <div className="score-pct">{pct}%</div>
      </div>

      {/* ── Per-round breakdown ────────────────────────────────────────── */}
      <div className="rounds-breakdown">
        <h2>Detalii pe runde</h2>
        <div className="rounds-list">
          {rounds.map((r) => {
            const status = r.titleCorrect && r.artistCorrect
              ? 'correct'
              : r.titleCorrect
              ? 'partial'
              : 'wrong';
            return (
              <div key={r.roundNumber} className={`round-row round-row--${status}`}>
                <span className="round-num">#{r.roundNumber}</span>
                <div className="round-song">
                  <span className="round-title">{r.correctTitle}</span>
                  <span className="round-artist">{r.correctArtist}</span>
                </div>
                <div className="round-flags">
                  <span className={r.titleCorrect ? 'flag--ok' : 'flag--miss'} title="Titlu">T</span>
                  <span className={r.artistCorrect ? 'flag--ok' : 'flag--miss'} title="Artist">A</span>
                </div>
                <span className="round-pts">+{r.pointsEarned}</span>
              </div>
            );
          })}
        </div>
      </div>

      <button className="new-game-btn" onClick={onNewGame}>
        Joc nou 🔄
      </button>
    </div>
  );
}
