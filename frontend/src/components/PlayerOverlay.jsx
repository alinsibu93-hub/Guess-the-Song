import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useYouTubePlayer } from '../hooks/useYouTubePlayer';
import './PlayerOverlay.css';

export default function PlayerOverlay({ videoId, startTime, duration, active, onEnded }) {
  const containerRef = useRef(null);
  const { isReady, play, stop } = useYouTubePlayer(containerRef);

  const [hasStarted,  setHasStarted]  = useState(false);
  const [isPlaying,   setIsPlaying]   = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(null);

  // Reset when a new round's video arrives.
  useEffect(() => {
    setHasStarted(false);
    setIsPlaying(false);
    setSecondsLeft(null);
    stop();
  }, [videoId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stop if parent deactivates mid-clip.
  useEffect(() => { if (!active) stop(); }, [active]); // eslint-disable-line

  // Unmount cleanup.
  useEffect(() => () => stop(), []); // eslint-disable-line

  // Visible countdown — ticks only after audio confirmed playing.
  useEffect(() => {
    if (!isPlaying) return;
    const tick = setInterval(() => {
      setSecondsLeft((s) => {
        if (s === null || s <= 1) { clearInterval(tick); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [isPlaying]);

  // ── CRITICAL: play() called synchronously inside onClick ─────────────────
  // Do NOT call play() via setState → useEffect. React scheduling (~100 ms)
  // expires Chrome's user-gesture window and audio is blocked.
  const handleTapPlay = useCallback(() => {
    if (!isReady || !videoId || !active || hasStarted) return;
    setHasStarted(true);
    play(
      videoId, startTime, duration,
      () => { setIsPlaying(false); onEnded?.(); },
      () => { setIsPlaying(true); setSecondsLeft(duration); },
    );
  }, [isReady, videoId, startTime, duration, active, hasStarted, play, onEnded]);

  return (
    <div className={`player-overlay${active ? ' player-overlay--active' : ''}`}>

      {/*
       * Anti-spoiler layout:
       *   1. .player-iframe-wrap  — full-size, holds the real YouTube iframe
       *   2. .player-cover        — dark CSS layer on top, hides video content
       *   3. .player-visual       — our UI (button / waveform / countdown) above cover
       *
       * Why visible at full size: Chrome blocks audio autoplay for iframes that
       * are outside the viewport or have display:none / opacity:0 / tiny size.
       * Full-size + covered = audio allowed + video hidden.
       */}
      <div ref={containerRef} className="player-iframe-wrap" aria-hidden="true" />
      <div className="player-cover" />

      <div className="player-visual">
        {!isReady && (
          <div className="player-status">
            <span className="spinner--sm" />
            <span>Se inițializează playerul...</span>
          </div>
        )}

        {isReady && active && !hasStarted && (
          <button className="tap-play-btn" onClick={handleTapPlay} aria-label="Pornește clipul audio">
            ▶ Ascultă
          </button>
        )}

        {isReady && active && hasStarted && !isPlaying && (
          <div className="player-status">
            <span className="spinner--sm" />
            <span>Se încarcă...</span>
          </div>
        )}

        {isReady && active && isPlaying && (
          <>
            <div className="player-wave" aria-label="Se redă audio">
              {[...Array(5)].map((_, i) => (
                <span key={i} className="wave-bar" />
              ))}
            </div>
            <p className="player-label">Ascultă cu atenție...</p>
            <div
              className={`countdown${secondsLeft !== null && secondsLeft <= 3 ? ' countdown--urgent' : ''}`}
              aria-live="polite"
            >
              <span className="countdown-number">{secondsLeft ?? duration}</span>
              <span className="countdown-unit">s</span>
            </div>
          </>
        )}

        {isReady && !active && (
          <div className="player-idle">
            <span className="player-idle-icon">🎧</span>
          </div>
        )}
      </div>
    </div>
  );
}
