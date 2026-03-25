import { useState } from 'preact/hooks';
import { Navbar } from './components/Navbar.jsx';
import { JobList } from './components/JobList.jsx';
import { PublishForm } from './components/PublishForm.jsx';
import { useJobs } from './hooks/useJobs.js';
import { useFavorites } from './hooks/useFavorites.js';
import { hasSigner } from './lib/nostr.js';

export function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPublish, setShowPublish] = useState(false);
  const { jobs, loading, error } = useJobs({ searchQuery });
  const { count: favCount } = useFavorites();

  const handlePublishSuccess = () => {
    // Toast notification
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = '✓ 职位已发布到 Nostr！';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };

  return (
    <div class="page">
      {/* Banner */}
      <div class="banner">
        <span class="banner-dot" />
        Nostr 去中心化招聘
        <span class="banner-dot" />
        开放 · 无需注册 · NIP-07 认证
        <span class="banner-dot" />
      </div>

      {/* Navbar */}
      <Navbar
        onSearch={setSearchQuery}
        onPublish={() => {
          if (!hasSigner()) {
            alert('请先安装 NIP-07 扩展（如 Alby 或 nos2x）来发布职位');
            return;
          }
          setShowPublish(true);
        }}
      />

      {/* Main Content */}
      <main class="main-content">
        <div class="container">
          {/* Hero */}
          <section class="hero">
            <p class="hero-eyebrow">Nostr · 去中心化 · 开放</p>
            <h1>
              在 <em>Nostr</em> 上<br />发现下一个机会
            </h1>
            <p class="hero-desc">
              AgentBoss 是基于 Nostr 协议的去中心化招聘平台。
              无需注册，无中心化平台，用你的 Nostr 公钥身份直接连接。
            </p>
          </section>

          {/* Jobs Layout */}
          <div class="jobs-layout">
            {/* Job Feed */}
            <div>
              <div class="jobs-section-title">
                <span>最新职位</span>
                <span style="color: var(--text-muted); font-size: 11px">
                  {loading ? '加载中...' : `${jobs.length} 个职位`}
                </span>
              </div>
              <JobList jobs={jobs} loading={loading} error={error} />
            </div>

            {/* Sidebar */}
            <aside class="sidebar">
              {/* Stats Widget */}
              <div class="sidebar-widget">
                <div class="sidebar-title">数据概览</div>
                <div class="stats-grid">
                  <div class="stat-item">
                    <div class="stat-value">{jobs.length}</div>
                    <div class="stat-label">职位</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{favCount}</div>
                    <div class="stat-label">收藏</div>
                  </div>
                </div>
              </div>

              {/* Tags Widget */}
              <div class="sidebar-widget">
                <div class="sidebar-title">热门标签</div>
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
                    ⚡ 需要 NIP-07 扩展
                  </div>
                  <p style="font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 12px">
                    安装浏览器扩展来签名发布职位：
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
        AgentBoss · Nostr 去中心化招聘 ·
        <a href="https://github.com/nicholasyangyang/AgentBoss" target="_blank" rel="noopener">
          GitHub
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
