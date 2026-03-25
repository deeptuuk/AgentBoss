import { useState } from 'preact/hooks';
import { useAuth } from '../hooks/useAuth.js';
import { LanguageSwitch } from './LanguageSwitch.jsx';
import { t } from '../lib/i18n.js';

export function Navbar({ onSearch, onPublish }) {
  const [searchValue, setSearchValue] = useState('');
  const { pubkey, hasSigner } = useAuth();

  const handleSearch = (e) => {
    setSearchValue(e.target.value);
    if (onSearch) onSearch(e.target.value);
  };

  return (
    <nav class="navbar">
      <div class="navbar-inner">
        <a href="#/" class="navbar-brand">
          <span class="navbar-logo">
            Agent<span>Boss</span>
          </span>
        </a>

        <div class="navbar-search">
          <span class="navbar-search-icon">⌕</span>
          <input
            type="search"
            placeholder={t('search_placeholder')}
            value={searchValue}
            onInput={handleSearch}
            aria-label={t('search_placeholder')}
          />
        </div>

        <div class="navbar-actions">
          <LanguageSwitch />

          {pubkey ? (
            <span class="pubkey-badge" title={pubkey}>
              ⚡ {pubkey.slice(0, 8)}…
            </span>
          ) : hasSigner ? (
            <span class="pubkey-badge" style="color: var(--accent)">
              {t('signing')}
            </span>
          ) : (
            <span class="pubkey-badge" style="color: var(--text-muted)">
              {t('disconnected')}
            </span>
          )}

          <button class="btn btn-primary" onClick={onPublish}>
            {t('publish_btn')}
          </button>
        </div>
      </div>
    </nav>
  );
}
