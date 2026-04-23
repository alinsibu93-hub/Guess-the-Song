import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useYouTubePlayer } from '../hooks/useYouTubePlayer';
import './PlayerOverlay.css';

export default function PlayerOverlay({ videoId, startTime, duration, active, onEnded }) {
  const containerRef = useRef(null);
  const { isReady, play, stop } = useYouTubePlayer(containerRef);

  // hasStarted: user tapped "▶ Ascultă" — guarantees a direct gesture for Chrome audio
  const [hasStarted, setHasStarted] = useState(false);
  // isPlaying: YouTube confirmed PLAYING — countdown starts from here, not from tap
  const [isPlaying, setIsPlaying] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(null);

  // Reset everything when a new round's video arrives.
  useEffect(() => {
    setHasStarted(false);
    setIsPlaying(false);
    setSecondsLeft(null);
  }, [videoId]);

  // Start playback only after user taps (hasStarted) and player is ready.
  useEffect(() => {
    if (!active || !isReady || !videoId || !hasStarted) return;

    play(
      videoId,
      startTime,
      duration,
      // onEnded — called by hook when clip duration expires
      () => {
        setIsPlaying(false);
        onEnded?.();
      },
      // onPlaybackStarted — called by hook on first PLAYING event (after buffering)
      // Countdown starts HERE, in sync with actual audio, not at tap time.
      () => {
        setIsPlaying(true);
        setSecondsLeft(duration);
      },
    );

    return () => {
      stop();
      setIsPlaying(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, isReady, videoId, startTime, duration, hasStarted]);

  // Visible countdown — ticks only while audio is confirmed playing.
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

  const handleTapPlay = useCallback(() => setHasStarted(true), []);

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

        {/* Step 1: player ready, waiting for user tap */}
        {isReady && active && !hasStarted && (
          <button className="tap-play-btn" onClick={handleTapPlay} aria-label="Pornește clipul audio">
            ▶ Ascultă
          </button>
        )}

        {/* Step 2: user tapped, video is buffering */}
        {isReady && active && hasStarted && !isPlaying && (
          <div className="player-status">
            <span className="spinner-sm" />
            <span>Se încarcă...</span>
          </div>
        )}

        {/* Step 3: audio confirmed playing — show waveform + countdown */}
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
