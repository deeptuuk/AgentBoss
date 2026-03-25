# AgentBoss Job Deletion — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 NIP-78 职位删除功能，修复 #39

---

## Task 1: 新建 useDeletedJobs hook

**Files:**
- Create: `web/src/hooks/useDeletedJobs.js`

- [ ] **Step 1: 实现 hook**

```javascript
const DELETED_KEY = 'agentboss_deleted_jobs';

function getDeleted() {
  try {
    return JSON.parse(localStorage.getItem(DELETED_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveDeleted(list) {
  localStorage.setItem(DELETED_KEY, JSON.stringify(list));
}

export function useDeletedJobs() {
  const isDeleted = (dTag) => getDeleted().includes(dTag);
  const markDeleted = (dTag) => {
    const list = getDeleted();
    if (!list.includes(dTag)) saveDeleted([...list, dTag]);
  };
  return { isDeleted, markDeleted };
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/hooks/useDeletedJobs.js
git commit -m "$(cat <<'EOF'
feat(web): add useDeletedJobs hook — localStorage deleted job filter

Tracks d_tags of deleted jobs locally for client-side filtering.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 添加 deleteJob 函数到 nostr.js

**Files:**
- Modify: `web/src/lib/nostr.js`

- [ ] **Step 1: 添加 import 和 deleteJob 函数**

```javascript
import { createRelayClient } from './relay.js';

export async function deleteJob(dTag, pubkey) {
  const event = {
    kind: 5,
    tags: [
      ['d', dTag],
      ['a', `30078:${pubkey}:${dTag}`],
    ],
    content: '',
    created_at: Math.floor(Date.now() / 1000),
  };
  const signed = await signEvent(event);
  const relay = createRelayClient();
  await relay.connect();
  await relay.publish(signed);
  relay.close();
  return signed;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/nostr.js
git commit -m "$(cat <<'EOF'
feat(web): add deleteJob — NIP-78 kind:5 deletion event

Signs and publishes kind:5 event referencing original job d_tag.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Update useJobs — 过滤已删除职位

**Files:**
- Modify: `web/src/hooks/useJobs.js`

- [ ] **Step 1: 导入 useDeletedJobs 并过滤**

```javascript
import { useDeletedJobs } from './useDeletedJobs.js';

export function useJobs({ province, city, searchQuery } = {}) {
  // ...
  const { isDeleted } = useDeletedJobs();

  // In EOSE callback, after filtering by searchQuery:
  const filtered = allJobs.filter((j) => !isDeleted(j.d_tag));
```

- [ ] **Step 2: 提交**

```bash
git add web/src/hooks/useJobs.js
git commit -m "$(cat <<'EOF'
feat(web): useJobs filters locally deleted jobs

Checks useDeletedJobs() isDeleted(d_tag) before rendering.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: 新建 DeleteModal 组件

**Files:**
- Create: `web/src/components/DeleteModal.jsx`

- [ ] **Step 1: 实现组件**

```jsx
import { t } from '../lib/i18n.js';

export function DeleteModal({ job, onConfirm, onClose }) {
  return (
    <div class="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h2 class="modal-title">{t('delete_title')}</h2>
          <button class="modal-close" onClick={onClose}>×</button>
        </div>
        <div style="padding: 20px;">
          <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 14px;">
            {t('delete_confirm')}
          </p>
          <div style="display: flex; gap: 12px;">
            <button class="btn btn-secondary" onClick={onClose}>
              {t('cancel')}
            </button>
            <button class="btn btn-danger" onClick={onConfirm}>
              {t('delete_confirm_btn')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/DeleteModal.jsx
git commit -m "$(cat <<'EOF'
feat(web): add DeleteModal — confirm job deletion

Modal with Cancel / Confirm buttons.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: JobCard 添加删除按钮

**Files:**
- Modify: `web/src/components/JobCard.jsx`
- Modify: `web/src/app.jsx`

- [ ] **Step 1: JobCard — 添加 onDelete prop 和删除按钮**

```jsx
export function JobCard({ job, onClick, onDelete }) {
  // ...

  return (
    <article onClick={onClick}>
      {/* ... existing content ... */}

      {onDelete && (
        <button
          class="job-delete"
          onClick={(e) => { e.stopPropagation(); onDelete(job); }}
          title={t('delete')}
        >
          🗑 {t('delete')}
        </button>
      )}
    </article>
  );
}
```

- [ ] **Step 2: App.jsx — 添加 DeleteModal 状态**

```jsx
const [deleteTarget, setDeleteTarget] = useState(null);
const { markDeleted } = useDeletedJobs();

const handleDeleteConfirm = async (job) => {
  const pubkey = /* from useAuth */;
  await deleteJob(job.d_tag, pubkey);
  markDeleted(job.d_tag);
  setDeleteTarget(null);
};
```

- [ ] **Step 3: App.jsx — 渲染 DeleteModal**

```jsx
{deleteTarget && (
  <DeleteModal
    job={deleteTarget}
    onConfirm={() => handleDeleteConfirm(deleteTarget)}
    onClose={() => setDeleteTarget(null)}
  />
)}
```

- [ ] **Step 4: App.jsx — 传递 onDelete 给 JobCard**

```jsx
<JobCard
  job={job}
  onClick={() => {}}
  onDelete={job.pubkey === pubkey ? (j) => setDeleteTarget(j) : undefined}
/>
```

- [ ] **Step 5: 提交**

```bash
git add web/src/components/JobCard.jsx web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): JobCard — add conditional delete button + DeleteModal

Only shown on own posts. Confirms before calling deleteJob + markDeleted.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 添加翻译 key

**Files:**
- Modify: `web/src/lib/i18n.js`

- [ ] **Step 1: 添加删除相关翻译**

```javascript
// zh
delete: '删除',
delete_title: '确认删除职位？',
delete_confirm: '删除后无法恢复。',
cancel: '取消',
delete_confirm_btn: '确认删除',

// en
delete: 'Delete',
delete_title: 'Delete this job?',
delete_confirm: 'This action cannot be undone.',
cancel: 'Cancel',
delete_confirm_btn: 'Confirm Delete',
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/i18n.js
git commit -m "$(cat <<'EOF'
feat(web): add deletion i18n keys — delete, confirm, cancel

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: 添加删除按钮样式

**Files:**
- Modify: `web/src/styles/index.css`

- [ ] **Step 1: 添加样式**

```css
.job-delete {
  background: none;
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}
.job-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.6);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add job-delete + btn-danger styles

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): NIP-78 job deletion — kind:5 + local filter (#39)" \
  --body "$(cat <<'EOF'
## Summary

Implement NIP-78 job deletion for Issue #39.

## Changes

- `useDeletedJobs.js`: localStorage hook tracking deleted d_tags
- `nostr.js`: `deleteJob()` — NIP-78 kind:5 event, signs + publishes
- `useJobs.js`: filters out locally deleted jobs
- `DeleteModal.jsx`: confirmation modal before deletion
- `JobCard.jsx`: delete button shown only on own posts
- `app.jsx`: DeleteModal state + handleDeleteConfirm flow
- `i18n.js`: delete, cancel, confirm translation keys
- `index.css`: `.job-delete` + `.btn-danger` styles

## Verification

- [ ] Delete button only visible on own posts
- [ ] Confirmation modal shows before deletion
- [ ] Deleted job disappears from list after confirmation
- [ ] Deletion persists after page refresh (localStorage)
- [ ] `npm test` passes

Closes #39.
EOF
)"
```

---

## 注意事项

- 删除按钮用 `e.stopPropagation()` 防止触发 JobCard 点击事件
- `deleteJob` 的 `content` 设为空字符串，NIP-78 规范不要求内容
- 本地过滤 MVP：V2 可考虑 relay 端查询 kind:5 删除事件
