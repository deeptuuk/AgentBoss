// Nostr utility — NIP-07 integration
import { bech32 } from 'bech32';
import { createRelayClient } from './relay.js';

/**
 * Get the Nostr signer (NIP-07 extension or none).
 * Throws if no extension is available.
 */
export function getSigner() {
  if (window.nostr && typeof window.nostr.signEvent === 'function') {
    return window.nostr;
  }
  throw new NoSignerError(
    'No NIP-07 extension found. Please install Alby (alby.com) or nos2x to sign events.'
  );
}

export class NoSignerError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NoSignerError';
  }
}

/**
 * Get public key from NIP-07 extension.
 */
export async function getPublicKey() {
  const signer = getSigner();
  return signer.getPublicKey();
}

/**
 * Sign an event with NIP-07 extension.
 */
export async function signEvent(event) {
  const signer = getSigner();
  return signer.signEvent(event);
}

/**
 * Check if user has a NIP-07 signer available.
 */
export function hasSigner() {
  return !!(window.nostr && typeof window.nostr.signEvent === 'function');
}

// ── Hex ↔ Bytes ──────────────────────────────────────────────────────────

/**
 * Convert a hex string to a Uint8Array of bytes.
 */
function hexToBytes(hex) {
  const len = hex.length >> 1;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = parseInt(hex.substring(i << 1, (i << 1) + 2), 16);
  }
  return bytes;
}

// ── Bech32 (npub/note) — via bech32 npm package ─────────────────────────────

/**
 * Encode a hex pubkey to npub format.
 * @param {string} hex - 64-character hex string
 * @returns {string} npub1... bech32 encoded string
 */
export function hexToNpub(hex) {
  const padded = hex.padStart(64, '0');
  const bytes = hexToBytes(padded);
  const words = bech32.toWords(bytes); // convertBits(bytes, 8, 5, true) → 52 groups
  return bech32.encode('npub', words);
}

/**
 * Decode an npub string back to hex pubkey.
 * @param {string} npub - npub1... bech32 string
 * @returns {string} 64-character hex string
 */
export function npubToHex(npub) {
  const { prefix, words } = bech32.decode(npub);
  if (prefix !== 'npub') throw new Error('Invalid npub: wrong prefix');
  const bytes = bech32.fromWords(words); // convertBits(words, 5, 8, false) → 33 bytes
  // fromWords returns 33 bytes (33×8=264 bits, last 4 bits are padding zeros)
  // The 33rd byte is just padding → drop it
  const hex = Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
  return hex.slice(0, 64);
}

/**
 * Truncate pubkey for display.
 */
export function shortPubkey(hex, len = 8) {
  if (!hex) return '';
  return `${hex.slice(0, len)}…`;
}

// ── NIP-78 Job Deletion ──────────────────────────────────────────────────

/**
 * Delete a job posting — NIP-78 kind:5 deletion event.
 * @param {string} dTag - The d tag of the job to delete
 * @param {string} pubkey - The author's pubkey
 */
export async function deleteJob(dTag, pubkey) {
  const event = {
    kind: 5,
    tags: [
      ['d', dTag],
      ['a', `30078:${pubkey}:${dTag}`],
    ],
    content: '',
    created_at: Math.floor(Date.now() / 1000),
  };
  const signed = await signEvent(event);
  const relay = createRelayClient();
  await relay.connect();
  await relay.publish(signed);
  relay.close();
  return signed;
}
