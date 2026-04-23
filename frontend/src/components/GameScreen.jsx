import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getCurrentRound, submitAnswer, getResults } from '../api/gameApi';
import PlayerOverlay from './PlayerOverlay';
import GuessInput from './GuessInput';
import FeedbackBanner from './FeedbackBanner';
import ProgressIndicator from './ProgressIndicator';

// ── UI state machine ───────────────────────────────────────────────────────
//
//   LOADING_ROUND → PLAYING → AWAITING_GUESS → SUBMITTING → FEEDBACK
//        ↑_____________________________|                        |
//                  (next round fetch)               gameComplete → GAME_OVER
//
const S = {
  LOADING_ROUND:  'LOADING_ROUND',   // fetching GET /round
  PLAYING:        'PLAYING',         // audio clip is running
  AWAITING_GUESS: 'AWAITING_GUESS',  // clip ended, waiting for player input
  SUBMITTING:     'SUBMITTING',      // POST /answer in flight
  FEEDBACK:       'FEEDBACK',        // showing round result
  ERROR:          'ERROR',           // unrecoverable error
};

/**
 * Orchestrates the full round lifecycle.
 *
 * Props:
 *   session    – { sessionId, totalRounds, mode, clipDuration, roundTimeout, difficulty }
 *   onGameOver – callback(results) when all rounds are complete
 */
export default function GameScreen({ session, onGameOver }) {
  const { sessionId, totalRounds, mode, difficulty } = session;

  const [uiState, setUiState]       = useState(S.LOADING_ROUND);
  const [round, setRound]           = useState(null);    // current RoundData
  const [lastResult, setLastResult] = useState(null);    // last AnswerResult
  const [score, setScore]           = useState(0);
  const [error, setError]           = useState(null);    // { message, transient }

  // Prevents duplicate in-flight fetch requests (e.g. StrictMode double-effect).
  const fetchingRef = useRef(false);

  // ── Fetch round ──────────────────────────────────────────────────────────
  const fetchRound = useCallback(async () => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    setUiState(S.LOADING_ROUND);
    setError(null);

    try {
      const data = await getCurrentRound(sessionId);

      // Backend signals game over via finished:true (not via HTTP status).
      if (data.finished) {
        const results = await getResults(sessionId);
        onGameOver(results);
        return;
      }

      setRound(data);
      setUiState(S.PLAYING);
    } catch (err) {
      showError(err, false);
    } finally {
      fetchingRef.current = false;
    }
  }, [sessionId, onGameOver]);

  // Fetch first round on mount.
  useEffect(() => {
    fetchRound();
    // fetchRound is stable (useCallback with stable deps).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Playback ended ───────────────────────────────────────────────────────
  // Called by PlayerOverlay after `duration` seconds elapse.
  function handlePlaybackEnd() {
    setUiState(S.AWAITING_GUESS);
  }

  // ── Submit answer ────────────────────────────────────────────────────────
  // payload: { choiceIndex } for MC mode, { title, artist? } for free_text.
  async function handleGuessSubmit(payload) {
    // Hard guard: only accept in AWAITING_GUESS. Prevents double-submit
    // from a stale closure or race between click and state update.
    if (uiState !== S.AWAITING_GUESS) return;

    setUiState(S.SUBMITTING);

    try {
      const result = await submitAnswer(sessionId, payload);
      setLastResult(result);
      setScore(result.totalScore);
      setUiState(S.FEEDBACK);
    } catch (err) {
      // Transient error: return to guess state so the player can retry.
      setUiState(S.AWAITING_GUESS);
      showError(err, true);
    }
  }

  // ── Advance to next round ────────────────────────────────────────────────
  // Called by FeedbackBanner (manual click or auto-timer).
  const handleNextRound = useCallback(() => {
    if (!lastResult) return;

    if (lastResult.gameComplete) {
      // All rounds done — fetch final results and hand off to App.
      getResults(sessionId).then(onGameOver).catch((err) => showError(err, false));
      return;
    }

    setLastResult(null);
    fetchRound();
  }, [lastResult, sessionId, onGameOver, fetchRound]);

  // ── Error helpers ────────────────────────────────────────────────────────
  function showError(err, transient) {
    const message = friendlyError(err);
    setError({ message, transient });
    if (!transient) setUiState(S.ERROR);
    // Auto-clear transient toasts after 4 s.
    if (transient) setTimeout(() => setError(null), 4000);
  }

  function friendlyError(err) {
    if (err.status === 404) return 'Sesiunea a expirat. Începe un joc nou.';
    if (err.status === 429) return 'Serviciul nu este disponibil momentan. Încearcă mâine.';
    if (err.status === 400) return 'Răspuns invalid. Încearcă din nou.';
    if (err.status >= 500)  return 'Eroare de server. Încearcă din nou.';
    return 'Problemă de conexiune. Verifică internetul.';
  }

  // ── Unrecoverable error screen ───────────────────────────────────────────
  if (uiState === S.ERROR) {
    return (
      <div className="error-screen">
        <p className="error-icon">⚠️</p>
        <p className="error-message">{error?.message}</p>
        <button className="error-btn" onClick={() => window.location.reload()}>
          Joc nou
        </button>
      </div>
    );
  }

  // ── Main render ──────────────────────────────────────────────────────────
  return (
    <div className="game-screen">

      {/* ── Progress ──────────────────────────────────────────────────────── */}
      <ProgressIndicator
        currentRound={round?.roundNumber ?? 1}
        totalRounds={totalRounds}
        score={score}
      />

      {/* ── Transient error toast ─────────────────────────────────────────── */}
      {error?.transient && (
        <div className="error-toast" role="alert">{error.message}</div>
      )}

      {/* ── Audio player ──────────────────────────────────────────────────
          Always mounted so the YouTube player stays alive across rounds.
          `active` drives whether it actually plays.
      */}
      <PlayerOverlay
        videoId={round?.videoId}
        startTime={round?.startTime ?? 0}
        duration={round?.duration ?? 8}
        active={uiState === S.PLAYING}
        onEnded={handlePlaybackEnd}
      />

      {/* ── Loading indicator ──────────────────────────────────────────────── */}
      {uiState === S.LOADING_ROUND && (
        <div className="loading-round">
          <span className="spinner-sm" />
          <span>Se încarcă runda…</span>
        </div>
      )}

      {/* ── Guess area ────────────────────────────────────────────────────
          Rendered in AWAITING_GUESS and SUBMITTING.
          `key` forces GuessInput to remount (and reset state) each new round.
          `disabled` blocks input while the POST /answer is in flight.
      */}
      {(uiState === S.AWAITING_GUESS || uiState === S.SUBMITTING) && (
        <div className="guess-area">
          <h2 className="guess-prompt">Ce piesă a fost?</h2>
          <GuessInput
            key={round?.roundNumber}
            mode={mode}
            choices={round?.choices}
            onSubmit={handleGuessSubmit}
            disabled={uiState === S.SUBMITTING}
            difficulty={difficulty}
          />
        </div>
      )}

      {/* ── Feedback banner ───────────────────────────────────────────────── */}
      {uiState === S.FEEDBACK && lastResult && (
        <FeedbackBanner
          result={lastResult}
          onNext={handleNextRound}
        />
      )}
    </div>
  );
}
