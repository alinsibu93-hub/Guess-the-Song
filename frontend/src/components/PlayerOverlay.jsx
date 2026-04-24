import React, { useRef, useEffect, useState, useCallback } from 'react';
import './PlayerOverlay.css';

/**
 * PlayerOverlay — HTML5 <audio> player for iTunes preview URLs.
 *
 * Why not YouTube IFrame? Chrome's autoplay policy blocks unmuted audio on
 * cross-origin iframes for low-MEI origins (any new Vercel/Netlify URL).
 * We got ~40% reliability after exhaustive workarounds. Native <audio>
 * plays reliably from any user gesture. No workarounds needed.
 *
 * Props:
 *   previewUrl        — iTunes .m4a preview URL (30s clip)
 *   duration          — seconds of the preview to play (8/15/3 by difficulty)
 *   active            — whether this player is the currently-active round
 *   onEnded           — callback when the clip finishes
 *   thumbnail         — optional artwork URL (shown while playing)
 */
export default function PlayerOverlay({ previewUrl, duration, active, onEnded, thumbnail }) {
  const audioRef    = useRef(null);
  const stopTimerRef = useRef(null);
  const endedCbRef   = useRef(onEnded);

  const [hasStarted,  setHasStarted]  = useState(false);
  const [isPlaying,   setIsPlaying]   = useState(false);
  const [hasError,    setHasError]    = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(null);

  // Keep the latest onEnded in a ref so stop timer uses the fresh closure.
  useEffect(() => { endedCbRef.current = onEnded; }, [onEnded]);

  // Reset when a new round's preview arrives.
  useEffect(() => {
    setHasStarted(false);
    setIsPlaying(false);
    setHasError(false);
    setSecondsLeft(null);
    clearTimeout(stopTimerRef.current);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, [previewUrl]);

  // Stop if parent deactivates mid-clip.
  useEffect(() => {
    if (!active && audioRef.current) {
      audioRef.current.pause();
      clearTimeout(stopTimerRef.current);
    }
  }, [active]);

  // Unmount cleanup.
  useEffect(() => () => clearTimeout(stopTimerRef.current), []);

  // Visible countdown — ticks only after audio is actually playing.
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

  // ── play() — called directly from the onClick handler ────────────────────
  // Browsers permit <audio>.play() from any user gesture, no ceremony.
  const handleTapPlay = useCallback(() => {
    if (!previewUrl || !active || hasStarted) return;
    setHasStarted(true);
    setHasError(false);

    const audio = audioRef.current;
    if (!audio) return;

    const playPromise = audio.play();
    // Older browsers don't return a promise; modern ones do.
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch((err) => {
        console.warn('[audio] play() rejected:', err);
        setHasError(true);
        // Delay before advancing — lets user read the message.
        stopTimerRef.current = setTimeout(() => endedCbRef.current?.(), 2000);
      });
    }
  }, [previewUrl, active, hasStarted]);

  // ── <audio> event handlers ───────────────────────────────────────────────
  const handlePlaying = useCallback(() => {
    setIsPlaying(true);
    setSecondsLeft(duration);

    // Schedule stop after `duration` seconds. Fresh timer per playback
    // so pause/resume edges don't accumulate.
    clearTimeout(stopTimerRef.current);
    stopTimerRef.current = setTimeout(() => {
      if (audioRef.current) audioRef.current.pause();
      setIsPlaying(false);
      endedCbRef.current?.();
    }, duration * 1000);
  }, [duration]);

  const handleError = useCallback(() => {
    console.warn('[audio] error event');
    setHasError(true);
    setIsPlaying(false);
    clearTimeout(stopTimerRef.current);
    stopTimerRef.current = setTimeout(() => endedCbRef.current?.(), 2000);
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className={`player-overlay${active ? ' player-overlay--active' : ''}`}>

      {/*
       * Native <audio> element. No autoplay — playback is triggered by the
       * user clicking "▶ Ascultă". `preload="auto"` gives the browser a
       * head start on buffering once we set src.
       *
       * display:none is fine for <audio> (unlike iframes) — browsers never
       * gate audio elements on visibility.
       */}
      <audio
        ref={audioRef}
        src={previewUrl || undefined}
        preload="auto"
        onPlaying={handlePlaying}
        onError={handleError}
        style={{ display: 'none' }}
      />

      <div className="player-visual">
        {active && !hasStarted && previewUrl && (
          <button className="tap-play-btn" onClick={handleTapPlay} aria-label="Pornește clipul audio">
            ▶ Ascultă
          </button>
        )}

        {active && hasStarted && !isPlaying && !hasError && (
          <div className="player-status">
            <span className="spinner--sm" />
            <span>Se încarcă...</span>
          </div>
        )}

        {active && hasError && (
          <div className="player-error">
            <span className="player-error-icon">⚠️</span>
            <span>Piesa nu este disponibilă. Se avansează...</span>
          </div>
        )}

        {active && isPlaying && (
          <>
            <div className="vinyl" aria-hidden="true">
              <div className="vinyl__label">
                <div className="vinyl__hole" />
              </div>
            </div>
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

        {!active && (
          <div className="player-idle">
            <span className="player-idle-icon">🎧</span>
          </div>
        )}
      </div>
    </div>
  );
}
