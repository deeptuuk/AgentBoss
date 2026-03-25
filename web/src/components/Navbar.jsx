import { useState } from 'preact/hooks';
import { useAuth } from '../hooks/useAuth.js';

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
            placeholder="搜索职位、公司..."
            value={searchValue}
            onInput={handleSearch}
            aria-label="搜索职位"
          />
        </div>

        <div class="navbar-actions">
          {pubkey ? (
            <span class="pubkey-badge" title={pubkey}>
              ⚡ {pubkey.slice(0, 8)}…
            </span>
          ) : hasSigner ? (
            <span class="pubkey-badge" style="color: var(--accent)">
              签名中...
            </span>
          ) : (
            <span class="pubkey-badge" style="color: var(--text-muted)">
              未连接
            </span>
          )}

          <button class="btn btn-primary" onClick={onPublish}>
            + 发布职位
          </button>
        </div>
      </div>
    </nav>
  );
}
