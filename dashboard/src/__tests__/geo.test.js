import { describe, it, expect } from 'vitest';
import { haversineDistance } from '../utils/geo';

describe('geo utils', () => {
  it('calculates distance between two points', () => {
    // ~111km for 1 degree of latitude
    const dist = haversineDistance(0, 0, 1, 0);
    expect(dist).toBeGreaterThan(110000);
    expect(dist).toBeLessThan(112000);
  });

  it('same point returns 0', () => {
    expect(haversineDistance(37.386, -122.084, 37.386, -122.084)).toBe(0);
  });
});
