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
 * Four-pillar strategy for reliable audio under Chrome's autoplay policy:
 *
 *   Pillar 1 — Iframe created MANUALLY with allow="autoplay; encrypted-media"
 *     YT.Player creates its iframe internally, which means `allow` set in
 *     onReady is read AFTER the iframe already loaded with default perms.
 *     We create the iframe ourselves with the right attributes at birth,
 *     then let YT.Player adopt it by passing the iframe's id.
 *
 *   Pillar 2 — cue(videoId, startTime)  [no gesture needed]
 *     Calls cueVideoById — metadata + buffer, does NOT play.
 *
 *   Pillar 3 — play(duration, …)  [MUST be called inside onClick]
 *     3a. mute() + playVideo() — muted autoplay is ALWAYS permitted,
 *                                regardless of MEI or origin trust.
 *     3b. On PLAYING state → unMute() + setVolume(100) — sticky activation
 *         from the click extends to this callback, so unmute succeeds.
 *
 *   Pillar 4 (UX) — requestUnmute()  [called from a fresh user click]
 *     If PlayerOverlay detects playback is still muted after 2 s, it shows
 *     a "🔊 Activează sunetul" button. Clicking it calls this in a fresh
 *     gesture context — last-ditch recovery for the edge cases where
 *     sticky activation didn't propagate through the cross-origin iframe.
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

      // ── Pillar 1: manual iframe with allow set at CREATION time ─────────
      // Chrome reads `allow` once, at iframe load. Setting it later (e.g.
      // in onReady) is effectively a no-op for already-loaded content.
      const iframeId = 'yt-player-' + Math.random().toString(36).slice(2, 10);
      const iframe = document.createElement('iframe');
      iframe.id = iframeId;
      iframe.setAttribute(
        'allow',
        'autoplay; encrypted-media; gyroscope; picture-in-picture',
      );
      iframe.setAttribute('allowfullscreen', '');
      iframe.setAttribute('frameborder', '0');
      iframe.width  = '100%';
      iframe.height = '100%';
      iframe.style.border = '0';
      iframe.style.display = 'block';

      // playerVars must go in the src query string since YT.Player will
      // adopt this iframe rather than generate a new one.
      const params = new URLSearchParams({
        enablejsapi:    '1',
        origin:         window.location.origin,
        controls:       '0',
        disablekb:      '1',
        fs:             '0',
        iv_load_policy: '3',
        modestbranding: '1',
        rel:            '0',
        playsinline:    '1',
        autoplay:       '0',
      });
      iframe.src = `https://www.youtube.com/embed/?${params.toString()}`;

      containerRef.current.appendChild(iframe);

      playerRef.current = new window.YT.Player(iframeId, {
        events: {
          onReady: () => {
            if (!destroyed) setIsReady(true);
          },

          onStateChange: (e) => {
            if (e.data !== 1 /* PLAYING */) return;
            if (!clipRef.current || clipRef.current.consumed) return;

            clipRef.current.consumed = true;
            clearTimeout(fallbackRef.current);

            // ── Pillar 3b: redundant unmute ───────────────────────────────
            // Belt-and-suspenders — if the unmute in play() didn't land
            // (edge case: very delayed buffering), try again here inside
            // sticky activation from the media element itself.
            try {
              e.target.unMute();
              e.target.setVolume(100);
            } catch (_) {}

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

  /** Phase 1 — pre-buffer without playing. No gesture required. */
  const cue = useCallback((videoId, startTime) => {
    if (!playerRef.current) return;
    try {
      playerRef.current.cueVideoById({ videoId, startSeconds: startTime });
    } catch (_) {}
  }, []);

  /** Phase 2 — start playback. MUST be called from inside an onClick handler. */
  const play = useCallback((duration, onEnded, onPlaybackStarted, onPlayError) => {
    if (!playerRef.current) return;

    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = { duration, onEnded, onPlaybackStarted, onPlayError, consumed: false };

    // ── Pillar 3a: UNMUTED-start in the same gesture ────────────────────
    // Critical insight: Chrome treats muted-autoplay and unmuted-play as
    // separate permission classes. Once a cross-origin iframe media starts
    // MUTED, Chrome refuses any subsequent unMute(), even from a fresh
    // gesture — empirically confirmed on low-MEI origins.
    //
    // Instead, we issue unMute() + setVolume(100) + playVideo() all within
    // the same onClick gesture. With allow="autoplay" set at iframe
    // creation (Pillar 1), Chrome delegates the parent gesture to the
    // iframe and permits unmuted playback.
    try {
      playerRef.current.unMute();
      playerRef.current.setVolume(100);
      playerRef.current.playVideo();
    } catch (_) {}

    // Safety net: if PLAYING never fires within 5 s, advance the round.
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

  /** Pillar 4 — last-ditch unmute from a fresh user gesture. */
  const requestUnmute = useCallback(() => {
    if (!playerRef.current) return;
    try {
      playerRef.current.unMute();
      playerRef.current.setVolume(100);
    } catch (_) {}
  }, []);

  /** Check mute state — used by UI to decide whether to show unmute button. */
  const isMuted = useCallback(() => {
    if (!playerRef.current) return false;
    try {
      return playerRef.current.isMuted() || playerRef.current.getVolume() === 0;
    } catch (_) { return false; }
  }, []);

  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    clearTimeout(fallbackRef.current);
    clipRef.current = null;
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, cue, play, stop, requestUnmute, isMuted };
}
