import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useDeletedJobs } from '../hooks/useDeletedJobs.js';
import { renderHook } from '@testing-library/preact';

describe('useDeletedJobs', () => {
  const STORAGE_KEY = 'agentboss_deleted_jobs';

  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it('isDeleted returns false for non-deleted dTag', () => {
    const { result } = renderHook(() => useDeletedJobs());
    expect(result.current.isDeleted('abc')).toBe(false);
  });

  it('markDeleted makes isDeleted return true', () => {
    const { result } = renderHook(() => useDeletedJobs());
    result.current.markDeleted('abc');
    expect(result.current.isDeleted('abc')).toBe(true);
  });

  it('isDeleted returns false for different dTag', () => {
    const { result } = renderHook(() => useDeletedJobs());
    result.current.markDeleted('abc');
    expect(result.current.isDeleted('xyz')).toBe(false);
  });

  it('persists across renders via localStorage', () => {
    const { result: r1 } = renderHook(() => useDeletedJobs());
    r1.current.markDeleted('tag123');

    const { result: r2 } = renderHook(() => useDeletedJobs());
    expect(r2.current.isDeleted('tag123')).toBe(true);
  });
});
