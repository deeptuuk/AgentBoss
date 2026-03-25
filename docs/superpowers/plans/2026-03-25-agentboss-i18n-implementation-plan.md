# AgentBoss 中英文切换 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 添加 i18n 框架，实现 Navbar ZH/EN 切换器，替换所有硬编码 UI 文本。

---

## Task 1: 创建 i18n 框架

**Files:**
- Create: `web/src/lib/i18n.js`

- [ ] **Step 1: 创建 web/src/lib/i18n.js**

```javascript
const STORAGE_KEY = 'agentboss_lang';

export const translations = {
  zh: {
    search_placeholder: '搜索职位、公司...',
    publish_btn: '+ 发布职位',
    signing: '签名中...',
    disconnected: '未连接',
    banner_text: 'Nostr 去中心化招聘',
    banner_sub: '开放 · 无需注册 · NIP-07 认证',
    hero_eyebrow: 'Nostr · 去中心化 · 开放',
    hero_title: '在 Nostr 上发现下一个机会',
    hero_desc: 'AgentBoss 是基于 Nostr 协议的去中心化招聘平台。无需注册，无中心化平台，用你的 Nostr 公钥身份直接连接。',
    latest_jobs: '最新职位',
    loading_jobs: '加载中...',
    jobs_count: '个职位',
    data_overview: '数据概览',
    jobs: '职位',
    favorites: '收藏',
    popular_tags: '热门标签',
    need_nip07: '⚡ 需要 NIP-07 扩展',
    install_ext: '安装浏览器扩展来签名发布职位：',
    footer_text: 'AgentBoss · Nostr 去中心化招聘',
    github: 'GitHub',
    favorite: '收藏',
    unfavorite: '取消收藏',
    empty_jobs: '暂无职位',
    empty_sub: '成为第一个发布职位的人吧',
    load_error: '加载失败',
    form_title: '发布职位',
    form_title_label: '职位名称 *',
    form_title_ph: '如：高级前端工程师',
    form_company_label: '公司名称 *',
    form_company_ph: '如：Nostr Labs',
    form_province_label: '省份 *',
    form_province_ph: '如：beijing',
    form_city_label: '城市 *',
    form_city_ph: '如：beijing',
    form_salary_label: '薪资范围',
    form_salary_ph: '如：30k-50k',
    form_desc_label: '职位描述',
    form_desc_ph: '描述职位要求、职责...',
    form_contact_label: '联系方式',
    form_contact_ph: 'NIP-05 邮箱或其他联系方式',
    form_contact_hint: '可在 contact 字段填写您的 NIP-05（如 alice@nostr.com）',
    form_submit: '发布中...',
    form_submit_btn: '⚡ 发布到 Nostr',
    err_title: '请填写职位名称',
    err_company: '请填写公司名称',
    err_province: '请填写省份',
    err_city: '请填写城市',
    err_nip07: '请先安装 NIP-07 扩展（如 Alby）来签名发布',
    err_post: '发布失败，请重试',
    success: '✓ 职位已发布到 Nostr！',
  },
  en: {
    search_placeholder: 'Search jobs, companies...',
    publish_btn: '+ Post Job',
    signing: 'Signing...',
    disconnected: 'Not connected',
    banner_text: 'Nostr Decentralized Jobs',
    banner_sub: 'Open · No registration · NIP-07 Auth',
    hero_eyebrow: 'Nostr · Decentralized · Open',
    hero_title: 'Find Your Next Opportunity on Nostr',
    hero_desc: 'AgentBoss is a decentralized job platform on Nostr. No registration, no central authority — connect with your Nostr public key.',
    latest_jobs: 'Latest Jobs',
    loading_jobs: 'Loading...',
    jobs_count: 'jobs',
    data_overview: 'Stats',
    jobs: 'Jobs',
    favorites: 'Favorites',
    popular_tags: 'Popular Tags',
    need_nip07: '⚡ NIP-07 Extension Required',
    install_ext: 'Install a browser extension to sign and post jobs:',
    footer_text: 'AgentBoss · Nostr Decentralized Jobs',
    github: 'GitHub',
    favorite: 'Favorite',
    unfavorite: 'Unfavorite',
    empty_jobs: 'No jobs yet',
    empty_sub: 'Be the first to post a job',
    load_error: 'Failed to load',
    form_title: 'Post a Job',
    form_title_label: 'Job Title *',
    form_title_ph: 'e.g.: Senior Frontend Engineer',
    form_company_label: 'Company Name *',
    form_company_ph: 'e.g.: Nostr Labs',
    form_province_label: 'Province *',
    form_province_ph: 'e.g.: beijing',
    form_city_label: 'City *',
    form_city_ph: 'e.g.: beijing',
    form_salary_label: 'Salary Range',
    form_salary_ph: 'e.g.: 30k-50k',
    form_desc_label: 'Job Description',
    form_desc_ph: 'Describe requirements, responsibilities...',
    form_contact_label: 'Contact',
    form_contact_ph: 'NIP-05 email or other contact',
    form_contact_hint: 'Your NIP-05 (e.g. alice@nostr.com)',
    form_submit: 'Posting...',
    form_submit_btn: '⚡ Post to Nostr',
    err_title: 'Job title is required',
    err_company: 'Company name is required',
    err_province: 'Province is required',
    err_city: 'City is required',
    err_nip07: 'Please install a NIP-07 extension (e.g. Alby) to sign and post',
    err_post: 'Failed to post, please try again',
    success: '✓ Job posted to Nostr!',
  },
};

let _lang = localStorage.getItem(STORAGE_KEY) || 'zh';

export function t(key, params = {}) {
  let text = translations[_lang][key] ?? key;
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, v);
  }
  return text;
}

export function getLang() {
  return _lang;
}

export function setLang(lang) {
  _lang = lang;
  localStorage.setItem(STORAGE_KEY, lang);
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/i18n.js
git commit -m "$(cat <<'EOF'
feat(web): add i18n framework — zh/en translations

i18n.js with translations dict, t(), getLang(), setLang().
40+ keys covering all UI text. localStorage persistence.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 创建 LanguageSwitch 组件

**Files:**
- Create: `web/src/components/LanguageSwitch.jsx`

- [ ] **Step 1: 创建 LanguageSwitch.jsx**

```jsx
import { getLang, setLang } from '../lib/i18n.js';

export function LanguageSwitch() {
  const lang = getLang();

  const toggle = () => setLang(lang === 'zh' ? 'en' : 'zh');

  return (
    <button
      class="lang-switch"
      onClick={toggle}
      title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      <span class={lang === 'zh' ? 'lang-active' : 'lang-inactive'}>ZH</span>
      <span class="lang-sep">|</span>
      <span class={lang === 'en' ? 'lang-active' : 'lang-inactive'}>EN</span>
    </button>
  );
}
```

- [ ] **Step 2: 添加 LanguageSwitch 样式到 index.css**

在 `index.css` 末尾添加：

```css
/* Language Switch */
.lang-switch {
  background: none;
  border: none;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  letter-spacing: 0.05em;
  padding: 4px 8px;
  color: var(--text-muted);
  transition: color 0.2s;
}
.lang-switch:hover {
  color: var(--text);
}
.lang-active {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.lang-inactive {
  color: var(--text-muted);
}
.lang-sep {
  color: var(--border);
  margin: 0 2px;
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/LanguageSwitch.jsx web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add LanguageSwitch component — ZH/EN toggle

Compact text-based toggle in navbar right.
JetBrains Mono, active language underlined in amber.
Hover state transitions.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: 集成到 Navbar

**Files:**
- Modify: `web/src/components/Navbar.jsx`

- [ ] **Step 1: 更新 Navbar.jsx**

```jsx
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
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/Navbar.jsx
git commit -m "$(cat <<'EOF'
feat(web): integrate LanguageSwitch into Navbar

Replaced hardcoded text with t() calls.
Search placeholder, publish button, signer status all translated.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: 更新 App.jsx

**Files:**
- Modify: `web/src/app.jsx`

- [ ] **Step 1: 更新 app.jsx 中的所有 UI 文本**

替换 Banner、Hero、Sidebar、Footer 中的硬编码文本为 `t()` 调用。

- [ ] **Step 2: 提交**

```bash
git add web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): translate App.jsx — banner, hero, sidebar, footer

All hardcoded UI text replaced with t() calls.
Jobs count uses t('jobs_count').replace('{n}', jobs.length).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 更新 PublishForm.jsx

**Files:**
- Modify: `web/src/components/PublishForm.jsx`

- [ ] **Step 1: 更新 PublishForm.jsx**

替换所有 label、placeholder、按钮文本、错误提示为 `t()` 调用。

- [ ] **Step 2: 提交**

```bash
git add web/src/components/PublishForm.jsx
git commit -m "$(cat <<'EOF'
feat(web): translate PublishForm — labels, placeholders, errors, buttons

All form text replaced with t() calls.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 更新 JobCard + JobList

**Files:**
- Modify: `web/src/components/JobCard.jsx`
- Modify: `web/src/components/JobList.jsx`

- [ ] **Step 1: JobCard — 收藏按钮文本使用 t()**

```jsx
<button
  class={`job-favorite ${fav ? 'active' : ''}`}
  onClick={handleFav}
  title={fav ? t('unfavorite') : t('favorite')}
  aria-label={fav ? t('unfavorite') : t('favorite')}
>
  {fav ? '★' : '☆'}
</button>
```

- [ ] **Step 2: JobList — 状态文本使用 t()**

```jsx
{loading && <div class="jobs-grid">{[1,2,3,4].map(i => <div key={i} class="skeleton job-card-skeleton" />)}</div>}

{error && (
  <div class="empty-state">
    <div class="empty-state-icon">⚠</div>
    <h3>{t('load_error')}</h3>
    <p>{error}</p>
  </div>
)}

{!jobs.length && !loading && (
  <div class="empty-state">
    <div class="empty-state-icon">📭</div>
    <h3>{t('empty_jobs')}</h3>
    <p>{t('empty_sub')}</p>
  </div>
)}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/JobCard.jsx web/src/components/JobList.jsx
git commit -m "$(cat <<'EOF'
feat(web): translate JobCard and JobList

Favorite/unfavorite button, empty/loading/error states all translated.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): add zh/en language switch — i18n framework" \
  --body "$(cat <<'EOF'
## Summary

Add ZH/EN language switch to AgentBoss frontend.

## Changes

- `web/src/lib/i18n.js`: Translation dict + `t()` + `getLang/setLang`
- `web/src/components/LanguageSwitch.jsx`: ZH | EN toggle component
- `web/src/styles/index.css`: Language switch styles (JetBrains Mono, amber active state)
- `web/src/components/Navbar.jsx`: Integrate LangSwitch, replace text with `t()`
- `web/src/app.jsx`: Banner, hero, sidebar, footer translated
- `web/src/components/PublishForm.jsx`: All form text translated
- `web/src/components/JobCard.jsx`: Favorite button translated
- `web/src/components/JobList.jsx`: Empty/loading/error states translated

## Verification

- [ ] ZH/EN toggle visible in navbar
- [ ] Switching language updates all UI text instantly
- [ ] Language choice persists after page refresh
- [ ] No untranslated hardcoded strings remain

Closes #27.
EOF
)"
```

---

## 注意事项

- `app.jsx` 中 `{jobs.length} 个职位` 改为 `${jobs.length} ${t('jobs_count')}`
- `app.jsx` 中 `"加载中..."` 改为 `t('loading_jobs')`
- 切换后页面需重新渲染，确保 App 组件内使用 `getLang()` 的地方能响应语言变化
- 如果需要强制刷新，可监听语言切换事件，或在 App 顶层加 `key={getLang()}` 触发重渲染
