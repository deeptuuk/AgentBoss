import { useState, useEffect } from 'preact/hooks';
import { Navbar } from './components/Navbar.jsx';
import { JobList } from './components/JobList.jsx';
import { PublishForm } from './components/PublishForm.jsx';
import { useJobs } from './hooks/useJobs.js';
import { useFavorites } from './hooks/useFavorites.js';
import { hasSigner } from './lib/nostr.js';
import { t, getLang, subscribeToLang } from './lib/i18n.js';

export function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPublish, setShowPublish] = useState(false);
  // Force re-render when language changes via subscribeToLang
  const [_langVersion, setLangVersion] = useState(0);
  const { jobs, loading, error } = useJobs({ searchQuery });
  const { count: favCount } = useFavorites();

  // Subscribe to language changes — triggers re-render on switch
  useEffect(() => {
    const unsub = subscribeToLang(() => setLangVersion((v) => v + 1));
    return unsub;
  }, []);

  // Read language once to keep unused variable lint happy
  void getLang();

  const handlePublishClick = () => {
    if (!hasSigner()) {
      alert(t('err_alert_nip07'));
      return;
    }
    setShowPublish(true);
  };

  const handlePublishSuccess = () => {
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = t('success');
    document.body.appendChild(toast);
    setTimeout(() => {
      setShowPublish(false);
      toast.remove();
    }, 2500);
  };

  return (
    <div class="page">
      {/* Banner */}
      <div class="banner">
        <span class="banner-dot" />
        {t('banner_text')}
        <span class="banner-dot" />
        {t('banner_sub')}
        <span class="banner-dot" />
      </div>

      {/* Navbar */}
      <Navbar
        onSearch={setSearchQuery}
        onPublish={handlePublishClick}
      />

      {/* Main Content */}
      <main class="main-content">
        <div class="container">
          {/* Hero */}
          <section class="hero">
            <p class="hero-eyebrow">{t('hero_eyebrow')}</p>
            <h1 dangerouslySetInnerHTML={{ __html: t('hero_title') }} />
            <p class="hero-desc">{t('hero_desc')}</p>
          </section>

          {/* Jobs Layout */}
          <div class="jobs-layout">
            {/* Job Feed */}
            <div>
              <div class="jobs-section-title">
                <span>{t('latest_jobs')}</span>
                <span style="color: var(--text-muted); font-size: 11px">
                  {loading ? t('loading_jobs') : `${jobs.length} ${t('jobs_count')}`}
                </span>
              </div>
              <JobList jobs={jobs} loading={loading} error={error} />
            </div>

            {/* Sidebar */}
            <aside class="sidebar">
              {/* Stats Widget */}
              <div class="sidebar-widget">
                <div class="sidebar-title">{t('data_overview')}</div>
                <div class="stats-grid">
                  <div class="stat-item">
                    <div class="stat-value">{jobs.length}</div>
                    <div class="stat-label">{t('jobs')}</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{favCount}</div>
                    <div class="stat-label">{t('favorites')}</div>
                  </div>
                </div>
              </div>

              {/* Tags Widget */}
              <div class="sidebar-widget">
                <div class="sidebar-title">{t('popular_tags')}</div>
                <div class="tag-cloud">
                  <button class="cloud-tag" onClick={() => setSearchQuery('remote')}>🌍 Remote</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('engineering')}>💻 Engineering</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('beijing')}>🏙 Beijing</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('shanghai')}>🏙 Shanghai</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('30k')}>💰 30k+</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('senior')}>⭐ Senior</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('frontend')}>⚛ Frontend</button>
                  <button class="cloud-tag" onClick={() => setSearchQuery('design')}>🎨 Design</button>
                </div>
              </div>

              {/* NIP-07 Info */}
              {!hasSigner() && (
                <div class="sidebar-widget" style="border-color: var(--accent-border)">
                  <div class="sidebar-title" style="color: var(--accent)">
                    {t('need_nip07')}
                  </div>
                  <p style="font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 12px">
                    {t('install_ext')}
                  </p>
                  <div style="display: flex; flex-direction: column; gap: 8px;">
                    <a
                      href="https://alby.com"
                      target="_blank"
                      rel="noopener"
                      class="btn btn-ghost"
                      style="font-size: 12px; justify-content: center;"
                    >
                      Alby（推荐）
                    </a>
                    <a
                      href="https://nos2x.kkreunt.com"
                      target="_blank"
                      rel="noopener"
                      class="btn btn-ghost"
                      style="font-size: 12px; justify-content: center;"
                    >
                      nos2x
                    </a>
                  </div>
                </div>
              )}
            </aside>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer class="footer">
        {t('footer_text')} ·
        <a href="https://github.com/nicholasyangyang/AgentBoss" target="_blank" rel="noopener">
          {t('github')}
        </a>
      </footer>

      {/* Publish Modal */}
      {showPublish && (
        <PublishForm
          onClose={() => setShowPublish(false)}
          onSuccess={handlePublishSuccess}
        />
      )}
    </div>
  );
}
