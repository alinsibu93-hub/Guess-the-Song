import React, { useRef, useEffect, useState } from 'react';
import { useYouTubePlayer } from '../hooks/useYouTubePlayer';
import './PlayerOverlay.css';

/**
 * Anti-spoiler audio player.
 *
 * The YouTube iframe is positioned off-screen (left: -9999px) so the user
 * never sees the video title or thumbnail. Audio plays normally.
 * A custom countdown UI replaces the native player.
 *
 * Props:
 *   videoId   – YouTube video ID for this round
 *   startTime – seconds at which playback begins (from backend)
 *   duration  – clip length in seconds (equals session's clipDuration)
 *   active    – true while we should be playing (PLAYING state in GameScreen)
 *   onEnded   – called when the clip finishes (transitions to AWAITING_GUESS)
 */
export default function PlayerOverlay({ videoId, startTime, duration, active, onEnded }) {
  const containerRef = useRef(null);
  const { isReady, play, stop } = useYouTubePlayer(containerRef);
  const [secondsLeft, setSecondsLeft] = useState(null);

  useEffect(() => {
    // Only trigger when we have everything needed and active flips to true.
    if (!active || !isReady || !videoId) return;

    setSecondsLeft(duration);

    play(videoId, startTime, duration, () => {
      setSecondsLeft(0);
      onEnded?.();
    });

    // Visible countdown ticker — independent of the actual audio timer.
    const tick = setInterval(() => {
      setSecondsLeft((s) => {
        if (s === null || s <= 1) { clearInterval(tick); return 0; }
        return s - 1;
      });
    }, 1000);

    return () => {
      clearInterval(tick);
      // Stop audio if this effect is cleaned up before the clip ends
      // (e.g. component unmount or videoId change mid-play).
      stop();
    };
    // Re-run only when a new clip should start.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, isReady, videoId, startTime, duration]);

  return (
    <div className={`player-overlay${active ? ' player-overlay--active' : ''}`}>
      {/* ── Hidden YouTube iframe ─────────────────────────────────────────
          Off-screen so no title, thumbnail, or branding is ever visible.
          aria-hidden removes it from the accessibility tree.
      */}
      <div
        ref={containerRef}
        style={{ position: 'absolute', left: '-9999px', width: 1, height: 1 }}
        aria-hidden="true"
      />

      {/* ── Custom visual UI ──────────────────────────────────────────────
          Replaces the YouTube player entirely in the visible layout.
      */}
      <div className="player-visual">
        {!isReady && (
          <div className="player-status">
            <span className="spinner-sm" />
            <span>Se inițializează playerul...</span>
          </div>
        )}

        {isReady && active && (
          <>
            <div className="player-wave" aria-label="Se redă audio">
              {/* Simple animated bars — replace with a real waveform if desired */}
              {[...Array(5)].map((_, i) => (
                <span key={i} className="wave-bar" style={{ animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
            <p className="player-label">Ascultă cu atenție...</p>
            <div className={`countdown${secondsLeft !== null && secondsLeft <= 3 ? ' countdown--urgent' : ''}`} aria-live="polite" aria-label={`${secondsLeft} secunde rămase`}>
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
