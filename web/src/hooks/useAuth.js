import { useState, useEffect } from 'preact/hooks';
import { getPublicKey, hasSigner, shortPubkey } from '../lib/nostr.js';

export function useAuth() {
  const [pubkey, setPubkey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hasSigner()) {
      setLoading(false);
      return;
    }

    getPublicKey()
      .then((pk) => {
        setPubkey(pk);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return {
    pubkey,
    loading,
    error,
    hasSigner: hasSigner(),
    shortPubkey: pubkey ? shortPubkey(pubkey) : null,
  };
}
