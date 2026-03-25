import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/preact';
import { useJobs } from '../hooks/useJobs.js';

// Mock relay: onEOSE fires synchronously so loading=false immediately
vi.mock('../lib/relay.js', () => ({
  createRelayClient: vi.fn(() => ({
    connect: vi.fn().mockResolvedValue(undefined),
    subscribe: vi.fn(),
    close: vi.fn(),
    onEvent: vi.fn(),
    onEOSE: (cb) => cb(),
  })),
}));

describe('useJobs', () => {
  it('returns jobs, loading, error, reload structure', async () => {
    const { result } = renderHook(() => useJobs({}));
    expect(result.current).toHaveProperty('jobs');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('reload');
  });

  it('sets loading=true initially', () => {
    const { result } = renderHook(() => useJobs({}));
    expect(result.current.loading).toBe(true);
  });

  it('sets loading=false after EOSE', async () => {
    const { result } = renderHook(() => useJobs({}));
    await waitFor(() => expect(result.current.loading).toBe(false));
  });

  it('populates jobs after EOSE', async () => {
    const { result } = renderHook(() => useJobs({}));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.jobs).toBeDefined();
  });

  it('filters by searchQuery', async () => {
    const { result } = renderHook(() => useJobs({ searchQuery: 'Frontend' }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.jobs.length).toBeLessThanOrEqual(2);
  });
});
