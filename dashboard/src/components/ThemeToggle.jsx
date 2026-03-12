import React, { useEffect } from 'react';
import { useSwarmState } from '../context/WebSocketContext';

export default function ThemeToggle() {
  const { state, dispatch } = useSwarmState();

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' && state.darkMode) {
      dispatch({ type: 'TOGGLE_DARK_MODE' });
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      state.darkMode ? 'dark' : 'light'
    );
    localStorage.setItem('theme', state.darkMode ? 'dark' : 'light');
  }, [state.darkMode]);

  return (
    <button
      className="theme-toggle"
      data-testid="theme-toggle"
      onClick={() => dispatch({ type: 'TOGGLE_DARK_MODE' })}
      aria-label="Toggle dark mode"
    >
      {state.darkMode ? '☀️' : '🌙'}
    </button>
  );
}
