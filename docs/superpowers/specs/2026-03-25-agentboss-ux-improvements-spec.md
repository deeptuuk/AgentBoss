# AgentBoss UI/UX 改进 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved
**Issue:** #33

---

## 1. 背景

代码审查发现三个影响体验的简单问题，收益明显，成本低。

## 2. 目标

- Search 输入防抖 500ms
- Navbar hexToNpub 变量缓存
- 表单提交成功后 toast 显示完再 close

---

## 3. 技术方案

### 3.1 Search 防抖

在 `Navbar.jsx` 中处理 debounce，不修改 `useJobs`：

```jsx
import { useState, useRef } from 'preact/hooks';

export function Navbar({ onSearch, onPublish }) {
  const [searchValue, setSearchValue] = useState('');
  const debounceRef = useRef(null);

  const handleSearch = (e) => {
    setSearchValue(e.target.value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (onSearch) onSearch(e.target.value);
    }, 500);
  };
  // ...
}
```

**优势：** 防抖逻辑封装在 Navbar，不污染 useJobs hook。

### 3.2 hexToNpub 变量缓存

```jsx
const npub = pubkey ? hexToNpub(pubkey) : null;

{pubkey ? (
  <span class="pubkey-badge" title={npub}>
    ⚡ {npub.slice(0, 12)}…
  </span>
) : ...}
```

### 3.3 表单提交成功后再 close

修改 `PublishForm.jsx` 的 `onSuccess` 行为，传递 `delayClose` 回调：

```jsx
const handleSuccess = () => {
  if (onSuccess) onSuccess();
  // Don't close immediately — let toast display
};

// App.jsx: handlePublishSuccess calls onSuccess which sets showPublish(false)
// with a delay or via event
```

简化方案：App.jsx 的 `handlePublishSuccess` 中，不在 `onSuccess` 立即 close，而是延迟：

```jsx
const handlePublishSuccess = () => {
  const toast = document.createElement('div');
  toast.className = 'toast success';
  toast.textContent = t('success');
  document.body.appendChild(toast);
  setShowPublish(false); // close modal immediately (toast lives on body)
};
```

等 toast 显示后再 close 改法更简单：移除 `onClose()` 调用，toast 挂在 `document.body` 上，modal 已 close 不影响。

---

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/components/Navbar.jsx` | 添加 debounce（useRef + setTimeout）|
| `web/src/components/Navbar.jsx` | 抽取 `npub` 变量 |
| `web/src/app.jsx` | 表单成功后立即 close，toast 不受影响 |

---

## 5. 验证标准

- [ ] 输入停止 500ms 后才触发 search
- [ ] hexToNpub 调用一次而非两次
- [ ] 提交成功后 toast 仍在屏幕显示
- [ ] 现有测试全部通过
