import { describe, it, expect } from 'vitest';
import { reducer, initialState } from '../../context/WebSocketContext';

describe('SPEC 18 — Dark Mode', () => {
  it('defaults to dark mode', () => {
    expect(initialState.darkMode).toBe(true);
  });

  it('toggle switches to light mode', () => {
    const state = reducer(initialState, { type: 'TOGGLE_DARK_MODE' });
    expect(state.darkMode).toBe(false);
  });

  it('toggle back to dark mode', () => {
    let state = reducer(initialState, { type: 'TOGGLE_DARK_MODE' });
    state = reducer(state, { type: 'TOGGLE_DARK_MODE' });
    expect(state.darkMode).toBe(true);
  });
});
