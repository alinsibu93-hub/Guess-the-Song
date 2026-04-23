import React, { useRef, useEffect, useState, useCallback } from 'react';
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
  // hasStarted: user has tapped the play button — guarantees a direct gesture
  // before loadVideoById, which Chrome requires for audio on new sites.
  const [hasStarted, setHasStarted] = useState(false);

  // Reset tap state when a new round loads.
  useEffect(() => {
    setHasStarted(false);
    setSecondsLeft(null);
  }, [videoId]);

  useEffect(() => {
    if (!active || !isReady || !videoId || !hasStarted) return;

    setSecondsLeft(duration);

    play(videoId, startTime, duration, () => {
      setSecondsLeft(0);
      onEnded?.();
    });

    const tick = setInterval(() => {
      setSecondsLeft((s) => {
        if (s === null || s <= 1) { clearInterval(tick); return 0; }
        return s - 1;
      });
    }, 1000);

    return () => {
      clearInterval(tick);
      stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, isReady, videoId, startTime, duration, hasStarted]);

  const handleTapPlay = useCallback(() => {
    setHasStarted(true);
  }, []);

  return (
    <div className={`player-overlay${active ? ' player-overlay--active' : ''}`}>
      <div
        ref={containerRef}
        style={{ position: 'absolute', left: '-9999px', width: 1, height: 1 }}
        aria-hidden="true"
      />

      <div className="player-visual">
        {!isReady && (
          <div className="player-status">
            <span className="spinner-sm" />
            <span>Se inițializează playerul...</span>
          </div>
        )}

        {/* Tap-to-play button — direct user gesture required by Chrome for audio */}
        {isReady && active && !hasStarted && (
          <button className="tap-play-btn" onClick={handleTapPlay} aria-label="Pornește clipul audio">
            ▶ Ascultă
          </button>
        )}

        {isReady && active && hasStarted && (
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
