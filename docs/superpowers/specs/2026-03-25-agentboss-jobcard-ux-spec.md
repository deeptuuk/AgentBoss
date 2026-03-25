# JobCard 和 JobList UX 改进 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved
**Issue:** #35

---

## 1. 背景

三个影响用户体验和转化的简单问题。

## 2. 技术方案

### 2.1 JobList 重试按钮

```jsx
{error && (
  <div class="empty-state">
    <div class="empty-state-icon">⚠</div>
    <h3>{t('load_error')}</h3>
    <p>{error}</p>
    <button class="btn btn-secondary" onClick={onJobClick}>
      {t('retry')}
    </button>
  </div>
)}
```

传入 `reload` prop 到 JobList，或通过 `useJobs` 返回的 `reload` 函数。

简化方案：`useJobs` 已在 App 层，可通过 `JobList` props 传递：

```jsx
<JobList jobs={jobs} loading={loading} error={error} onReload={reload} />
```

### 2.2 空状态 CTA

```jsx
{!jobs.length && !loading && (
  <div class="empty-state">
    <div class="empty-state-icon">📭</div>
    <h3>{t('empty_jobs')}</h3>
    <p>{t('empty_sub')}</p>
    <button class="btn btn-primary" onClick={onPublish}>
      {t('publish_btn')}
    </button>
  </div>
)}
```

### 2.3 JobCard 联系方式

```jsx
{job.contact && (
  <div class="job-contact">
    <span class="job-contact-label">{t('contact')}: </span>
    {job.contact.includes('@') ? (
      <a href={`mailto:${job.contact}`}>{job.contact}</a>
    ) : (
      <span>{job.contact}</span>
    )}
  </div>
)}
```

样式：`.job-contact` 小字显示在卡片底部，联系方式旁加 📧 图标。

---

## 3. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/app.jsx` | 传递 `onPublish` + `reload` 到 JobList |
| `web/src/components/JobList.jsx` | error 状态重试按钮 + 空状态 CTA |
| `web/src/components/JobCard.jsx` | contact 字段展示 |
| `web/src/lib/i18n.js` | 新增 `retry` / `contact` 翻译 key |

---

## 4. 翻译 key

| Key | ZH | EN |
|-----|----|----|
| retry | 重试 | Retry |
| contact | 联系方式 | Contact |

---

## 5. 验证标准

- [ ] 加载失败时显示重试按钮
- [ ] 空状态底部有 CTA 按钮
- [ ] JobCard 显示 contact 信息
- [ ] `npm test` 通过
