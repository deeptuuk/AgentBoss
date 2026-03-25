// Nostr utility — NIP-07 integration

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

/**
 * Get npub from hex pubkey (Bech32 encoding).
 */
export function hexToNpub(hex) {
  // Simplified: return truncated hex for display
  // Full implementation would use bech32 encoding
  return hex;
}

/**
 * Truncate pubkey for display.
 */
export function shortPubkey(hex, len = 8) {
  if (!hex) return '';
  return `${hex.slice(0, len)}…`;
}
