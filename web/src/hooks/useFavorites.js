import { useState, useCallback } from 'preact/hooks';

const FAVORITES_KEY = 'agentboss_favorites';

function loadFavorites() {
  try {
    return JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveFavorites(favorites) {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
}

export function useFavorites() {
  const [favorites, setFavorites] = useState(() => new Set(loadFavorites()));

  const toggleFavorite = useCallback((eventId) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      saveFavorites([...next]);
      return next;
    });
  }, []);

  const isFavorite = useCallback((eventId) => favorites.has(eventId), [favorites]);

  return { favorites, toggleFavorite, isFavorite, count: favorites.size };
}
