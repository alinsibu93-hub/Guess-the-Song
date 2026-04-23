import { useEffect, useRef, useState, useCallback } from 'react';

// ── Singleton API loader ───────────────────────────────────────────────────
let ytApiPromise = null;

function loadYouTubeIframeApi() {
  if (ytApiPromise) return ytApiPromise;

  ytApiPromise = new Promise((resolve) => {
    if (window.YT?.Player) { resolve(); return; }

    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { previous?.(); resolve(); };

    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
  });

  return ytApiPromise;
}

// ── Hook ──────────────────────────────────────────────────────────────────
/**
 * play(videoId, startTime, duration, onEnded, onPlaybackStarted)
 *   - onEnded:          called when the clip window expires
 *   - onPlaybackStarted called on the FIRST PLAYING event after play() —
 *                       use this to start the visible countdown in sync with audio
 *
 * Only the FIRST PLAYING event per play() call starts the timer.
 * Subsequent PLAYING events (e.g. from YouTube auto-resume) are ignored.
 */
export function useYouTubePlayer(containerRef) {
  const playerRef      = useRef(null);
  const stopTimerRef   = useRef(null);
  const clipRef        = useRef(null);  // { duration, onEnded, onPlaybackStarted, consumed }
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
            if (e.data !== window.YT.PlayerState.PLAYING) return;
            if (!clipRef.current || clipRef.current.consumed) return;

            // Mark consumed so only the FIRST PLAYING event per play() call
            // starts the timer. Stale events from previous rounds are ignored.
            clipRef.current.consumed = true;

            e.target.unMute();
            e.target.setVolume(100);

            const { duration, onEnded, onPlaybackStarted } = clipRef.current;

            // Signal PlayerOverlay that audio has actually started — it can
            // now start the visible countdown in sync with real playback.
            onPlaybackStarted?.();

            clearTimeout(stopTimerRef.current);
            stopTimerRef.current = setTimeout(() => {
              try { playerRef.current?.pauseVideo(); } catch (_) {}
              clipRef.current = null;
              onEnded?.();
            }, duration * 1000);
          },

          onError: (e) => {
            console.warn('[YouTube] Player error code:', e.data);
            // Advance game on error so the user is never stuck on a broken clip.
            if (clipRef.current) {
              clipRef.current.onEnded?.();
              clipRef.current = null;
            }
          },
        },
      });
    });

    return () => {
      destroyed = true;
      clearTimeout(stopTimerRef.current);
      try { playerRef.current?.destroy(); } catch (_) {}
      playerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const play = useCallback((videoId, startTime, duration, onEnded, onPlaybackStarted) => {
    if (!playerRef.current) return;

    clearTimeout(stopTimerRef.current);
    // consumed: false — only the first PLAYING event for this clip is handled
    clipRef.current = { duration, onEnded, onPlaybackStarted, consumed: false };

    playerRef.current.unMute();
    playerRef.current.setVolume(100);
    playerRef.current.loadVideoById({ videoId, startSeconds: startTime });
  }, []);

  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    clipRef.current = null;
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, play, stop };
}
