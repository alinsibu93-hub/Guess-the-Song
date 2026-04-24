// Points to the Flask backend. The Vite proxy rewrites /api/* → localhost:5000
// in dev, so BASE_URL can stay empty. Set VITE_API_URL in .env for production.
const BASE_URL = import.meta.env?.VITE_API_URL ?? '';

/**
 * Internal fetch wrapper.
 * - Always sends / expects JSON.
 * - On non-2xx: throws an Error with .status and .body attached.
 */
async function apiFetch(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  // Parse body regardless of status so error messages are available.
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const error = new Error(body?.error ?? `HTTP ${response.status}`);
    error.status = response.status;
    error.body = body;
    throw error;
  }

  return body;
}

/**
 * POST /api/game/new
 * Creates a new game session and fetches all rounds from iTunes.
 * This call can take 5–30 s depending on round count.
 *
 * @returns {{ sessionId, totalRounds, difficulty, mode, clipDuration, roundTimeout }}
 */
export async function startGame({ rounds = 5, difficulty = 'normal', mode = 'multiple_choice' } = {}) {
  return apiFetch('/api/game/new', {
    method: 'POST',
    body: JSON.stringify({ rounds, difficulty, mode }),
  });
}

/**
 * GET /api/game/{sessionId}/round
 * Returns current round data, or { finished: true } when all rounds are done.
 *
 * Always check `data.finished` before reading other fields —
 * the shape changes when the game is complete.
 *
 * @returns {RoundData | { finished: true, totalRounds: number }}
 */
export async function getCurrentRound(sessionId) {
  return apiFetch(`/api/game/${sessionId}/round`);
}

/**
 * POST /api/game/{sessionId}/answer
 *
 * Multiple-choice payload: { choiceIndex: number }
 * Free-text payload:       { title: string, artist?: string }
 *
 * @returns {{ roundNumber, titleCorrect, artistCorrect, correctTitle,
 *             correctArtist, previewUrl, pointsEarned, totalScore, gameComplete }}
 */
export async function submitAnswer(sessionId, payload) {
  return apiFetch(`/api/game/${sessionId}/answer`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * GET /api/game/{sessionId}/results
 * @returns {{ sessionId, totalScore, maxPossibleScore, totalRounds, rounds: [] }}
 */
export async function getResults(sessionId) {
  return apiFetch(`/api/game/${sessionId}/results`);
}
