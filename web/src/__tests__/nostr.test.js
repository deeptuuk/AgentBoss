import { describe, it, expect } from 'vitest';
import { hexToNpub, npubToHex, shortPubkey, hasSigner } from '../lib/nostr.js';

describe('nostr utils', () => {
  describe('hexToNpub', () => {
    it('starts with npub1 prefix', () => {
      const hex = '0'.repeat(64);
      expect(hexToNpub(hex).startsWith('npub1')).toBe(true);
    });

    it('round-trips: npubToHex(hexToNpub(hex)) === hex', () => {
      const hex = 'a'.repeat(64);
      expect(npubToHex(hexToNpub(hex))).toBe(hex);
    });

    it('round-trips with real hex pubkey', () => {
      const hex = 'f'.repeat(64);
      expect(npubToHex(hexToNpub(hex))).toBe(hex);
    });

    it('throws on invalid npub prefix', () => {
      expect(() => npubToHex('nsec1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')).toThrow();
    });
  });

  describe('shortPubkey', () => {
    it('truncates to 8 chars by default', () => {
      expect(shortPubkey('a'.repeat(64))).toBe('aaaaaaaa…');
    });

    it('respects custom length', () => {
      expect(shortPubkey('a'.repeat(64), 4)).toBe('aaaa…');
    });

    it('returns empty string for falsy input', () => {
      expect(shortPubkey('')).toBe('');
      expect(shortPubkey(null)).toBe('');
      expect(shortPubkey(undefined)).toBe('');
    });
  });

  describe('hasSigner', () => {
    it('is a function', () => {
      expect(typeof hasSigner).toBe('function');
    });
  });
});
