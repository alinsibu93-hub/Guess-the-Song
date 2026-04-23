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
 * The iframe is rendered at full size inside .player-iframe-wrap,
 * covered by a CSS overlay — so Chrome sees a "normal" visible video
 * and allows autoplay with audio, while the user never sees the video.
 *
 * play(videoId, startTime, duration, onEnded, onPlaybackStarted)
 *   onPlaybackStarted — called when PLAYING event fires (audio confirmed)
 *   onEnded           — called after duration seconds of actual playback
 *
 * Fallback: if PLAYING never fires within 5 s, advance anyway.
 */
export function useYouTubePlayer(containerRef) {
  const playerRef    = useRef(null);
  const stopTimerRef = useRef(null);
  const fallbackRef  = useRef(null);
  const clipRef      = useRef(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let destroyed = false;

    loadYouTubeIframeApi().then(() => {
      if (destroyed || !containerRef.current) return;

      playerRef.current = new window.YT.Player(containerRef.current, {
        // Full-size player — CSS overlay hides the video content.
        // A visible, full-size iframe is required for Chrome to allow audio autoplay.
        width:  '100%',
        height: '100%',
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
            // Start muted — Chrome always allows muted autoplay regardless of
            // MEI score, gesture context, or iframe visibility rules.
            // We unmute in onStateChange(PLAYING) once video is confirmed playing.
            e.target.mute();
            e.target.setVolume(100); // volume ready for when we unmute
            if (!destroyed) setIsReady(true);
          },

          onStateChange: (e) => {
            if (e.data !== 1 /* PLAYING */) return;
            if (!clipRef.current || clipRef.current.consumed) return;

            clipRef.current.consumed = true;
            clearTimeout(fallbackRef.current);

            // Unmute here — this is the reliable moment. Chrome already allowed
            // the muted playback; switching to unmuted mid-play is always permitted.
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

          onError: (e) => {
            console.warn('[YouTube] error code:', e.data);
            if (!clipRef.current) return;
            const { onEnded, onPlayError } = clipRef.current;
            clipRef.current = null;
            clearTimeout(stopTimerRef.current);
            clearTimeout(fallbackRef.current);
            // Notify PlayerOverlay to show error message, then advance after 2 s.
            onPlayError?.();
            stopTimerRef.current = setTimeout(() => onEnded?.(), 2000);
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

  const play = useCallback((videoId, startTime, duration, onEnded, onPlaybackStarted, onPlayError) => {
    if (!playerRef.current) return;

    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = { duration, onEnded, onPlaybackStarted, onPlayError, consumed: false };

    // Load muted — Chrome allows muted autoplay unconditionally.
    // onStateChange(PLAYING) will unmute once playback is confirmed.
    playerRef.current.mute();
    playerRef.current.loadVideoById({ videoId, startSeconds: startTime });

    // Fallback if PLAYING event never fires (e.g. video unavailable).
    fallbackRef.current = setTimeout(() => {
      if (!clipRef.current || clipRef.current.consumed) return;
      clipRef.current.consumed = true;
      try { playerRef.current?.unMute(); playerRef.current?.setVolume(100); } catch (_) {}
      const { duration: d, onEnded: ended, onPlaybackStarted: started } = clipRef.current;
      started?.();
      stopTimerRef.current = setTimeout(() => {
        try { playerRef.current?.pauseVideo(); } catch (_) {}
        clipRef.current = null;
        ended?.();
      }, d * 1000);
    }, 5000);
  }, []);

  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = null;
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, play, stop };
}
