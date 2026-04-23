import React, { useState, useCallback } from 'react';
import StartScreen from './components/StartScreen';
import GameScreen from './components/GameScreen';
import ResultsScreen from './components/ResultsScreen';

/**
 * Root component. Manages top-level screen transitions.
 *
 * Screens:
 *   'start'   – game configuration form
 *   'game'    – active gameplay
 *   'results' – final scoreboard
 *
 * Session data flows: StartScreen → App (state) → GameScreen
 * Results data flows: GameScreen → App (state) → ResultsScreen
 */
export default function App() {
  const [screen, setScreen]   = useState('start');
  const [session, setSession] = useState(null);
  const [results, setResults] = useState(null);

  const handleGameStart = useCallback((sessionData) => {
    setSession(sessionData);
    setScreen('game');
  }, []);

  const handleGameOver = useCallback((resultsData) => {
    setResults(resultsData);
    setScreen('results');
  }, []);

  const handleNewGame = useCallback(() => {
    setSession(null);
    setResults(null);
    setScreen('start');
  }, []);

  return (
    <div className="app">
      {screen === 'start' && (
        <StartScreen onStart={handleGameStart} />
      )}
      {screen === 'game' && session && (
        <GameScreen session={session} onGameOver={handleGameOver} />
      )}
      {screen === 'results' && results && (
        <ResultsScreen results={results} onNewGame={handleNewGame} />
      )}
    </div>
  );
}
