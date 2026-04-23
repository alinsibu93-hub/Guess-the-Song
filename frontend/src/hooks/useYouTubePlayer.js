import { useEffect, useRef, useState, useCallback } from 'react';

// ── Singleton API loader ───────────────────────────────────────────────────
// The YouTube IFrame API must be loaded only once per page. A module-level
// promise ensures concurrent callers wait for the same load event.
let ytApiPromise = null;

function loadYouTubeIframeApi() {
  if (ytApiPromise) return ytApiPromise;

  ytApiPromise = new Promise((resolve) => {
    // Already loaded (e.g. Vite HMR re-run).
    if (window.YT?.Player) {
      resolve();
      return;
    }

    // YouTube calls this global when the API is ready. We chain it so
    // any pre-existing callback is not silently discarded.
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      previous?.();
      resolve();
    };

    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
  });

  return ytApiPromise;
}

// ── Hook ──────────────────────────────────────────────────────────────────
/**
 * Manages a single hidden YouTube IFrame Player for audio-only playback.
 *
 * Usage:
 *   const containerRef = useRef(null);
 *   const { isReady, play, stop } = useYouTubePlayer(containerRef);
 *
 *   // containerRef must be attached to a mounted div.
 *   <div ref={containerRef} style={{ position:'absolute', left:'-9999px' }} />
 *
 * The player is created once on mount and destroyed on unmount.
 * `play()` can be called repeatedly for subsequent rounds.
 */
export function useYouTubePlayer(containerRef) {
  const playerRef = useRef(null);
  const stopTimerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let destroyed = false;

    loadYouTubeIframeApi().then(() => {
      if (destroyed || !containerRef.current) return;

      playerRef.current = new window.YT.Player(containerRef.current, {
        // 1×1 px — exists in DOM so the API works, but invisible to the user.
        width: '1',
        height: '1',
        playerVars: {
          controls: 0,         // no native UI controls
          disablekb: 1,        // no keyboard shortcuts
          fs: 0,               // no fullscreen button
          iv_load_policy: 3,   // no video annotations
          modestbranding: 1,   // minimal YouTube logo
          rel: 0,              // no related-video panel at end
          autoplay: 0,         // we call playVideo() manually
          playsinline: 1,      // required for iOS inline audio
          origin: window.location.origin,
        },
        events: {
          onReady: (e) => {
            // Unmute immediately on creation — Chrome may create players muted
            // on sites with low Media Engagement Index (new/rarely visited sites).
            e.target.unMute();
            e.target.setVolume(100);
            if (!destroyed) setIsReady(true);
          },
          onStateChange: (e) => {
            // Re-assert volume when playback actually starts (state 1 = PLAYING).
            // Belt-and-suspenders: Chrome occasionally re-mutes on loadVideoById.
            if (e.data === window.YT.PlayerState.PLAYING) {
              e.target.unMute();
              e.target.setVolume(100);
            }
          },
          onError: (e) => {
            // Common codes: 2=bad videoId, 100=not found, 150=not embeddable.
            console.warn('[YouTube] Player error code:', e.data);
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
    // containerRef is a stable ref object — effect intentionally runs once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Seek to `startTime` in `videoId`, play for `duration` seconds, then pause.
   * Calls `onEnded` when the clip window expires.
   *
   * loadVideoById() autoplays. Modern browsers allow this because the user
   * triggered the game via a button click earlier in the same gesture chain.
   */
  const play = useCallback((videoId, startTime, duration, onEnded) => {
    if (!playerRef.current) return;

    // Cancel any running stop timer from a previous clip.
    clearTimeout(stopTimerRef.current);

    playerRef.current.unMute();
    playerRef.current.setVolume(100);
    playerRef.current.loadVideoById({
      videoId,
      startSeconds: startTime,
    });

    stopTimerRef.current = setTimeout(() => {
      try { playerRef.current?.pauseVideo(); } catch (_) {}
      onEnded?.();
    }, duration * 1000);
  }, []);

  /**
   * Immediately pause and cancel the stop timer.
   * Call this if the component unmounts mid-playback.
   */
  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, play, stop };
}
