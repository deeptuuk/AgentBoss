# AgentBoss Unified Toast Notification System — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** useToast hook + ToastContainer，替换 alert()，统一 toast 通知，修复 #44

---

## Task 1: 新建 useToast Hook

**Files:**
- Create: `web/src/hooks/useToast.js`

- [ ] **Step 1: 实现 hook**

```javascript
import { useState } from 'preact/hooks';

export function useToast() {
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);

    if (type !== 'error') {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3000);
    }
  };

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return { toasts, showToast, dismissToast };
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/hooks/useToast.js
git commit -m "$(cat <<'EOF'
feat(web): add useToast hook — reusable toast notifications

showToast(message, type), auto-dismiss success after 3s,
error requires manual dismiss.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 新建 ToastContainer 组件

**Files:**
- Create: `web/src/components/ToastContainer.jsx`

- [ ] **Step 1: 实现组件**

```jsx
export function ToastContainer({ toasts, onDismiss }) {
  if (!toasts.length) return null;

  return (
    <div class="toast-container" role="region" aria-label="Notifications">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          class={`toast ${toast.type === 'error' ? 'toast-error' : 'toast-success'}`}
          onClick={() => toast.type === 'error' && onDismiss(toast.id)}
        >
          <span>{toast.message}</span>
          {toast.type === 'error' && (
            <button class="toast-close-btn" onClick={() => onDismiss(toast.id)}>×</button>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/ToastContainer.jsx
git commit -m "$(cat <<'EOF'
feat(web): add ToastContainer — fixed-position stacked toasts

Auto-dismiss success after 3s, error toasts need manual close.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: 添加翻译 key

**Files:**
- Modify: `web/src/lib/i18n.js`

- [ ] **Step 1: 添加 toast 相关 key**

```javascript
// zh
toast_published: '✓ 职位已发布到 Nostr！',
toast_deleted: '✓ 职位已删除',
toast_edited: '✓ 职位已更新',
toast_delete_err: '✗ 删除失败，请重试',
toast_nip07_err: '请先安装 NIP-07 扩展来使用此功能',

// en
toast_published: '✓ Job posted to Nostr!',
toast_deleted: '✓ Job deleted',
toast_edited: '✓ Job updated',
toast_delete_err: '✗ Failed to delete, please try again',
toast_nip07_err: 'Please install a NIP-07 extension to use this feature',
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/i18n.js
git commit -m "$(cat <<'EOF'
feat(web): add toast i18n keys — published, deleted, edited, errors

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: App.jsx — ToastContainer + 替换 alert()

**Files:**
- Modify: `web/src/app.jsx`

- [ ] **Step 1: 导入 ToastContainer**

```jsx
import { ToastContainer } from './components/ToastContainer.jsx';
```

- [ ] **Step 2: 添加 useToast**

```jsx
const { toasts, showToast, dismissToast } = useToast();
```

- [ ] **Step 3: 渲染 ToastContainer（在 return 的 JSX 末尾，</div> 前）**

```jsx
<ToastContainer toasts={toasts} onDismiss={dismissToast} />
```

- [ ] **Step 4: 替换 alert() — handlePublishClick**

```jsx
const handlePublishClick = () => {
  if (!hasSigner()) {
    showToast(t('toast_nip07_err'), 'error');
    return;
  }
  setShowPublish(true);
};
```

- [ ] **Step 5: handlePublishSuccess — 替换 toast**

```jsx
const handlePublishSuccess = () => {
  showToast(t('toast_published'), 'success');
  setTimeout(() => {
    setShowPublish(false);
  }, 2500);
};
```

删除原来的手动 DOM toast 代码：

```jsx
// 删除这段：
const toast = document.createElement('div');
toast.className = 'toast success';
toast.textContent = t('success');
document.body.appendChild(toast);
setTimeout(() => toast.remove(), 3000);
```

- [ ] **Step 6: handleDeleteConfirm — 添加 toast**

```jsx
const handleDeleteConfirm = async (job) => {
  try {
    await deleteJob(job.d_tag, pubkey);
    showToast(t('toast_deleted'), 'success');
  } catch {
    showToast(t('toast_delete_err'), 'error');
  }
  markDeleted(job.d_tag);
  setDeleteTarget(null);
};
```

- [ ] **Step 7: 删除 handlePublishSuccess 中的 old toast DOM 代码**

（原有的 `document.createElement` 手动 toast 移除）

- [ ] **Step 8: 提交**

```bash
git add web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): replace alert() + manual DOM toast with useToast

handlePublishClick: alert → showToast(error)
handlePublishSuccess: remove document.createElement toast → showToast
handleDeleteConfirm: add showToast(success) + showToast(error)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: CSS 样式

**Files:**
- Modify: `web/src/styles/index.css`

- [ ] **Step 1: 添加 toast 样式**

```css
/* ── Toast ─────────────────────────────── */
.toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 9999;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  pointer-events: all;
  max-width: 320px;
  background: var(--bg-secondary);
  animation: toast-in 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast-success {
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #86efac;
}

.toast-error {
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  cursor: pointer;
}

.toast-close-btn {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  margin-left: auto;
  opacity: 0.7;
}
.toast-close-btn:hover { opacity: 1; }

@keyframes toast-in {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add toast container + toast styles — success/error variants

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: PublishForm — 编辑成功后 toast（通过 onSuccess 回调）

PublishForm 编辑成功后调用 `onSuccess`，App.jsx 的 `handleEditSuccess` 添加 toast：

- [ ] **Step 1: App.jsx 添加 handleEditSuccess**

```jsx
const handleEditSuccess = () => {
  showToast(t('toast_edited'), 'success');
  setEditingJob(null);
  reload();
};
```

传入 PublishForm 的 `onSuccess`：

```jsx
<PublishForm
  jobToEdit={editingJob}
  onClose={() => setEditingJob(null)}
  onSuccess={handleEditSuccess}
/>
```

- [ ] **Step 2: 提交**

```bash
git add web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): add toast for job edited success

handleEditSuccess → showToast(t('toast_edited'))

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
  --title "feat(web): unified toast system — useToast + ToastContainer (#44)" \
  --body "$(cat <<'EOF'
## Summary

Replace alert() + manual DOM toast with unified useToast hook + ToastContainer.

## Changes

- `useToast.js`: hook with showToast(message, type) — success auto-dismiss 3s, error manual close
- `ToastContainer.jsx`: fixed top-right, stacked, animated
- `app.jsx`:
  - `handlePublishClick`: alert() → showToast(error)
  - `handlePublishSuccess`: remove document.createElement toast → showToast(success)
  - `handleDeleteConfirm`: add showToast(success/error)
  - `handleEditSuccess`: showToast(t('toast_edited'), 'success')
- `i18n.js`: 5 toast keys (published, deleted, edited, errors)
- `index.css`: .toast-container, .toast-success, .toast-error, animation

## Verification

- [ ] No alert() calls remain
- [ ] Publish → success toast
- [ ] Delete → success toast
- [ ] Edit → success toast
- [ ] NIP-07 error → error toast (manual close)
- [ ] Delete error → error toast (manual close)
- [ ] Multiple toasts stack correctly
- [ ] `npm test` passes

Closes #44.
EOF
)"
```

---

## 注意事项

- 移除 `handlePublishSuccess` 中原来的 `document.createElement` 手动 toast 代码
- `showToast` 的 `type` 只接受 `'success'` 或 `'error'`，不传默认 `'success'`
- ToastContainer 渲染在 `<div class="page">` 内部，page 之外也可以（只要是 fixed position）
