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
export function useYouTubePlayer(containerRef) {
  const playerRef    = useRef(null);
  const stopTimerRef = useRef(null);
  const clipInfoRef  = useRef(null); // { duration, onEnded } — set by play(), read by onStateChange
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let destroyed = false;

    loadYouTubeIframeApi().then(() => {
      if (destroyed || !containerRef.current) return;

      playerRef.current = new window.YT.Player(containerRef.current, {
        width: '1',
        height: '1',
        playerVars: {
          controls:        0,
          disablekb:       1,
          fs:              0,
          iv_load_policy:  3,
          modestbranding:  1,
          rel:             0,
          autoplay:        1,   // lets loadVideoById play immediately
          playsinline:     1,   // required for iOS inline audio
          origin:          window.location.origin,
        },
        events: {
          onReady: (e) => {
            // Force unmute on creation — Chrome mutes players on new/low-MEI sites.
            e.target.unMute();
            e.target.setVolume(100);
            if (!destroyed) setIsReady(true);
          },

          onStateChange: (e) => {
            if (e.data === window.YT.PlayerState.PLAYING) {
              // Timer starts here — from actual playback start, not from the API call.
              // This skips buffering time so the user hears the full clip duration.
              e.target.unMute();
              e.target.setVolume(100);

              if (clipInfoRef.current) {
                const { duration, onEnded } = clipInfoRef.current;
                clearTimeout(stopTimerRef.current);
                stopTimerRef.current = setTimeout(() => {
                  try { playerRef.current?.pauseVideo(); } catch (_) {}
                  onEnded?.();
                }, duration * 1000);
              }
            }
          },

          onError: (e) => {
            console.warn('[YouTube] Player error code:', e.data);
            // On error, still advance the game so the user isn't stuck.
            clipInfoRef.current?.onEnded?.();
            clipInfoRef.current = null;
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

  /**
   * Load and play a clip. The stop timer starts only once onStateChange
   * fires with PLAYING — so buffering time is not counted against the clip.
   */
  const play = useCallback((videoId, startTime, duration, onEnded) => {
    if (!playerRef.current) return;

    clearTimeout(stopTimerRef.current);
    clipInfoRef.current = { duration, onEnded };

    playerRef.current.unMute();
    playerRef.current.setVolume(100);
    playerRef.current.loadVideoById({ videoId, startSeconds: startTime });
  }, []);

  const stop = useCallback(() => {
    clearTimeout(stopTimerRef.current);
    clipInfoRef.current = null;
    try { playerRef.current?.pauseVideo(); } catch (_) {}
  }, []);

  return { isReady, play, stop };
}
