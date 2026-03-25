import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/preact';
import { useFavorites } from '../hooks/useFavorites.js';

const localStorageMock = {
  getItem: vi.fn().mockReturnValue('[]'),
  setItem: vi.fn(),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

describe('useFavorites', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockReturnValue('[]');
    localStorageMock.setItem.mockClear();
  });

  it('starts with count=0', () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.count).toBe(0);
  });

  it('adds favorite on toggle', () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.count).toBe(1);
  });

  it('removes favorite on second toggle', () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite('job1'));
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.count).toBe(0);
  });

  it('isFavorite returns correct value', () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.isFavorite('job1')).toBe(false);
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.isFavorite('job1')).toBe(true);
  });
});
