import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useYouTubePlayer } from '../hooks/useYouTubePlayer';
import './PlayerOverlay.css';

export default function PlayerOverlay({ videoId, startTime, duration, active, onEnded }) {
  const containerRef = useRef(null);
  const { isReady, play, stop } = useYouTubePlayer(containerRef);

  const [hasStarted, setHasStarted] = useState(false);
  const [isPlaying,  setIsPlaying]  = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(null);

  // Reset state when a new round's video arrives.
  useEffect(() => {
    setHasStarted(false);
    setIsPlaying(false);
    setSecondsLeft(null);
    stop();
  }, [videoId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stop playback if the parent deactivates us mid-clip.
  useEffect(() => {
    if (!active) stop();
  }, [active]); // eslint-disable-line react-hooks/exhaustive-deps

  // Unmount cleanup.
  useEffect(() => () => stop(), []); // eslint-disable-line react-hooks/exhaustive-deps

  // Visible countdown ticker — only while audio is confirmed playing.
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

  // ── Tap handler ────────────────────────────────────────────────────────
  // IMPORTANT: play() is called DIRECTLY here, synchronously inside the
  // click event handler. If we called it via setState → useEffect, the
  // ~100 ms React scheduling delay would expire Chrome's user-gesture
  // window and block audio entirely. Direct call = gesture window intact.
  const handleTapPlay = useCallback(() => {
    if (!isReady || !videoId || !active || hasStarted) return;
    setHasStarted(true);

    play(
      videoId,
      startTime,
      duration,
      // onEnded — clip window expired
      () => {
        setIsPlaying(false);
        onEnded?.();
      },
      // onPlaybackStarted — YouTube confirmed PLAYING; start visual countdown
      () => {
        setIsPlaying(true);
        setSecondsLeft(duration);
      },
    );
  }, [isReady, videoId, startTime, duration, active, hasStarted, play, onEnded]);

  return (
    <div className={`player-overlay${active ? ' player-overlay--active' : ''}`}>
      {/*
       * Iframe positioned at top:0 left:0 with opacity:0 — keeps it inside
       * Chrome's "visible viewport" check (required for autoplay to work)
       * while remaining invisible to the user. left:-9999px was blocking audio.
       */}
      <div
        ref={containerRef}
        style={{
          position: 'fixed',
          top: 0, left: 0,
          width: '1px', height: '1px',
          overflow: 'hidden',
          opacity: 0,
          pointerEvents: 'none',
          zIndex: -1,
        }}
        aria-hidden="true"
      />

      <div className="player-visual">
        {!isReady && (
          <div className="player-status">
            <span className="spinner--sm" />
            <span>Se inițializează playerul...</span>
          </div>
        )}

        {/* Waiting for tap */}
        {isReady && active && !hasStarted && (
          <button className="tap-play-btn" onClick={handleTapPlay} aria-label="Pornește clipul audio">
            ▶ Ascultă
          </button>
        )}

        {/* Tapped — buffering */}
        {isReady && active && hasStarted && !isPlaying && (
          <div className="player-status">
            <span className="spinner--sm" />
            <span>Se încarcă...</span>
          </div>
        )}

        {/* Audio confirmed playing */}
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
              aria-label={`${secondsLeft} secunde rămase`}
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
