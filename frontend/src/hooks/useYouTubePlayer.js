import { useEffect, useRef, useState, useCallback } from 'react';

// ── Singleton API loader ───────────────────────────────────────────────────
let ytApiPromise = null;

function loadYouTubeIframeApi() {
  if (ytApiPromise) return ytApiPromise;
  ytApiPromise = new Promise((resolve) => {
    if (window.YT?.Player) { resolve(); return; }
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { prev?.(); resolve(); };
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
  });
  return ytApiPromise;
}

// ── Hook ──────────────────────────────────────────────────────────────────
/**
 * play(videoId, startTime, duration, onEnded, onPlaybackStarted)
 *
 * Timer strategy:
 *   Primary   — starts when onStateChange(PLAYING) fires (audio is confirmed)
 *   Fallback  — starts 4 s after play() in case PLAYING event never arrives
 *               (Chrome sometimes suppresses it for off-screen iframes)
 *
 * consumed flag: only the FIRST PLAYING event per play() call is handled,
 * preventing stale events from a previous round restarting the timer.
 */
export function useYouTubePlayer(containerRef) {
  const playerRef    = useRef(null);
  const stopTimerRef = useRef(null);
  const fallbackRef  = useRef(null);
  const clipRef      = useRef(null); // { duration, onEnded, onPlaybackStarted, consumed }
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let destroyed = false;

    loadYouTubeIframeApi().then(() => {
      if (destroyed || !containerRef.current) return;

      playerRef.current = new window.YT.Player(containerRef.current, {
        width: '1',
        height: '1',
        playerVars: {
          controls:       0,
          disablekb:      1,
          fs:             0,
          iv_load_policy: 3,
          modestbranding: 1,
          rel:            0,
          autoplay:       1,
          playsinline:    1,
          origin:         window.location.origin,
        },
        events: {
          onReady: (e) => {
            e.target.unMute();
            e.target.setVolume(100);
            if (!destroyed) setIsReady(true);
          },

          onStateChange: (e) => {
            // Only handle the first PLAYING event per play() call.
            if (e.data !== 1 /* PLAYING */) return;
            if (!clipRef.current || clipRef.current.consumed) return;

            clipRef.current.consumed = true;
            clearTimeout(fallbackRef.current); // primary path — cancel fallback

            e.target.unMute();
            e.target.setVolume(100);

            const { duration, onEnded, onPlaybackStarted } = clipRef.current;
            onPlaybackStarted?.();

            clearTimeout(stopTimerRef.current);
            stopTimerRef.current = setTimeout(() => {
              try { playerRef.current?.pauseVideo(); } catch (_) {}
              clipRef.current = null;
              onEnded?.();
            }, duration * 1000);
          },

          onError: () => {
            // Advance the game so the user is never stuck on an unplayable clip.
            _advanceFromClip();
          },
        },
      });
    });

    return () => {
      destroyed = true;
      clearTimeout(stopTimerRef.current);
      clearTimeout(fallbackRef.current);
      try { playerRef.current?.destroy(); } catch (_) {}
      playerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Shared helper — fires onPlaybackStarted + onEnded immediately (fallback/error path).
  function _advanceFromClip() {
    if (!clipRef.current) return;
    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    const { onEnded, onPlaybackStarted, consumed } = clipRef.current;
    clipRef.current = null;
    if (!consumed) onPlaybackStarted?.(); // show waveform briefly
    onEnded?.();
  }

  const play = useCallback((videoId, startTime, duration, onEnded, onPlaybackStarted) => {
    if (!playerRef.current) return;

    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = { duration, onEnded, onPlaybackStarted, consumed: false };

    playerRef.current.unMute();
    playerRef.current.setVolume(100);
    playerRef.current.loadVideoById({ videoId, startSeconds: startTime });

    // Fallback: if onStateChange(PLAYING) never fires within 4 s (e.g. because
    // Chrome suppressed the event for the off-screen iframe), force-start the
    // countdown and timer so the user is never stuck at "Se încarcă...".
    fallbackRef.current = setTimeout(() => {
      if (!clipRef.current || clipRef.current.consumed) return;
      clipRef.current.consumed = true;

      try { playerRef.current?.unMute(); playerRef.current?.setVolume(100); } catch (_) {}
      clipRef.current.onPlaybackStarted?.();

      stopTimerRef.current = setTimeout(() => {
        try { playerRef.current?.pauseVideo(); } catch (_) {}
        clipRef.current = null;
        onEnded?.();
      }, duration * 1000);
    }, 4000);
  }, []);

  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = null;
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, play, stop };
}
