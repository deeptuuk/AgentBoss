# JobCard 和 JobList UX 改进 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重试按钮 + 空状态 CTA + JobCard 联系方式展示，修复 #35

---

## Task 1: 添加翻译 key

**Files:**
- Modify: `web/src/lib/i18n.js`

- [ ] **Step 1: 添加 retry 和 contact key**

在 zh/en 字典末尾添加：

```javascript
// zh
retry: '重试',
contact: '联系方式',

// en
retry: 'Retry',
contact: 'Contact',
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/i18n.js
git commit -m "$(cat <<'EOF'
feat(web): add retry + contact i18n keys

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: JobCard 联系方式展示

**Files:**
- Modify: `web/src/components/JobCard.jsx`

- [ ] **Step 1: 添加 contact 显示**

在卡片底部（时间显示附近）添加：

```jsx
{job.contact && (
  <div class="job-contact">
    📧 <span class="job-contact-text">{job.contact}</span>
  </div>
)}
```

- [ ] **Step 2: 添加 CSS 样式到 index.css**

```css
/* Job Contact */
.job-contact {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
}
.job-contact a {
  color: var(--accent);
  text-decoration: none;
}
.job-contact a:hover {
  text-decoration: underline;
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/JobCard.jsx web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): show contact field in JobCard

Displays NIP-05 email or other contact info.
Email rendered as mailto: link.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: JobList 重试按钮 + 空状态 CTA

**Files:**
- Modify: `web/src/components/JobList.jsx`
- Modify: `web/src/app.jsx`

- [ ] **Step 1: JobList 接收 onRetry prop**

```jsx
export function JobList({ jobs, loading, error, onRetry, onPublish }) {
```

- [ ] **Step 2: error 状态添加重试按钮**

```jsx
{error && (
  <div class="empty-state">
    <div class="empty-state-icon">⚠</div>
    <h3>{t('load_error')}</h3>
    <p>{error}</p>
    <button class="btn btn-secondary" onClick={onRetry}>
      {t('retry')}
    </button>
  </div>
)}
```

- [ ] **Step 3: 空状态添加 CTA 按钮**

```jsx
{!jobs.length && !loading && !error && (
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

- [ ] **Step 4: App.jsx 传递 props**

```jsx
<JobList
  jobs={jobs}
  loading={loading}
  error={error}
  onRetry={reload}
  onPublish={handlePublishClick}
/>
```

- [ ] **Step 5: 提交**

```bash
git add web/src/components/JobList.jsx web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): JobList retry button + empty state CTA

Error state: Retry button triggers reload.
Empty state: CTA button opens publish modal.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): JobList retry + empty CTA + JobCard contact (#35)" \
  --body "$(cat <<'EOF'
## Summary

Three UX improvements for JobCard and JobList (Issue #35).

## Changes

- `i18n.js`: `retry` + `contact` translation keys
- `JobCard.jsx`: Contact field displayed with 📧 icon, email as mailto: link
- `index.css`: `.job-contact` styles
- `JobList.jsx`: Error state retry button + empty state CTA button
- `app.jsx`: Pass `onRetry` + `onPublish` to JobList

## Verification

- [ ] Error state shows retry button
- [ ] Empty state shows CTA to post job
- [ ] JobCard displays contact info
- [ ] `npm test` passes

Closes #35.
EOF
)"
```

---

## 注意事项

- `onRetry` 从 `useJobs` 的 `reload` 传来，JobList 无需直接依赖 relay
- CTA 按钮使用 `btn btn-primary` 样式，与发布按钮一致
- contact 字段支持 mailto: link（检测是否包含 `@`）
