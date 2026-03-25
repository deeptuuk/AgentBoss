# AgentBoss UI/UX 改进 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Search 防抖 500ms + Navbar npub 变量缓存 + 表单成功即 close，修复 #33

---

## Task 1: Search 防抖

**Files:**
- Modify: `web/src/components/Navbar.jsx`

- [ ] **Step 1: 添加 useRef 导入**

```javascript
import { useState, useRef } from 'preact/hooks';
```

- [ ] **Step 2: 添加 debounce 逻辑**

```javascript
const debounceRef = useRef(null);

const handleSearch = (e) => {
  setSearchValue(e.target.value);
  clearTimeout(debounceRef.current);
  debounceRef.current = setTimeout(() => {
    if (onSearch) onSearch(e.target.value);
  }, 500);
};
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/Navbar.jsx
git commit -m "$(cat <<'EOF'
feat(web): Navbar search debounce 500ms

Prevents relay reconnect on every keystroke.
useRef + setTimeout, no external dependency.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Navbar npub 变量缓存

**Files:**
- Modify: `web/src/components/Navbar.jsx`

- [ ] **Step 1: 抽取 npub 变量**

在 Navbar 组件内，pubkey badge 处：

```javascript
const npub = pubkey ? hexToNpub(pubkey) : null;

{pubkey ? (
  <span class="pubkey-badge" title={npub}>
    ⚡ {npub.slice(0, 12)}…
  </span>
) : ...
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/Navbar.jsx
git commit -m "$(cat <<'EOF'
refactor(web): cache hexToNpub result in Navbar badge

Single call instead of duplicate hexToNpub(pubkey) in title + display.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: 表单提交成功后 toast 显示

**Files:**
- Modify: `web/src/app.jsx`

- [ ] **Step 1: 修改 handlePublishSuccess**

当前代码在 `onSuccess()` 后立即 `onClose()`，导致 modal 关闭。

修改 `handlePublishSuccess`，移除 `if (onClose) onClose()` 的立即调用：

```javascript
const handlePublishSuccess = () => {
  const toast = document.createElement('div');
  toast.className = 'toast success';
  toast.textContent = t('success');
  document.body.appendChild(toast);
  // Don't close immediately — toast displays on body, modal close is fine
  // But we should close the modal after the toast
  setTimeout(() => {
    setShowPublish(false);
    toast.remove();
  }, 2500);
};
```

同步修改 PublishForm 的调用（传递 onSuccess 即可，onClose 延迟由 App 控制）：

```jsx
<PublishForm
  onClose={() => setShowPublish(false)}
  onSuccess={handlePublishSuccess}
/>
```

- [ ] **Step 2: 提交**

```bash
git add web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): delay modal close after publish success — toast stays visible

Toast displays for 2.5s before modal closes and toast removes.
User sees confirmation before form disappears.

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
  --title "feat(web): search debounce + npub cache + toast confirmation (#33)" \
  --body "$(cat <<'EOF'
## Summary

Three UX improvements for Issue #33.

## Changes

- `Navbar.jsx`: Search input debounced 500ms via `useRef` + `setTimeout`
- `Navbar.jsx`: `hexToNpub` called once, result cached in `npub` variable
- `app.jsx`: Toast displays for 2.5s before modal closes — user sees confirmation

## Verification

- [ ] Typing in search box triggers relay query only after 500ms pause
- [ ] Navbar badge renders without duplicate hexToNpub calls
- [ ] Publishing job shows toast confirmation before modal disappears
- [ ] `npm test` passes

Closes #33.
EOF
)"
```

---

## 注意事项

- 防抖在 Navbar 层处理，不改动 useJobs hook
- toast 挂在 `document.body`，modal close 不影响 toast 显示
- 2.5s delay（比 toast 的 3s 稍短）确保 toast 还在时 modal 已关闭，体验流畅
