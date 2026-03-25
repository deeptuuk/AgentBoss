# AgentBoss Unified Toast Notification System — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-26
**Status:** Approved
**Issue:** #44

---

## 1. 背景

当前 app 使用 `alert()`（阻塞 UI）和手动 `document.createElement` 实现 toast，体验差且不可复用。

## 2. 目标

- 实现 `useToast` hook + `ToastContainer` 组件
- 替换所有 `alert()` 调用
- 统一发布/删除/编辑成功和错误通知

## 3. 技术方案

### 3.1 useToast Hook

```javascript
// web/src/hooks/useToast.js

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

### 3.2 ToastContainer Component

```jsx
// web/src/components/ToastContainer.jsx

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div class="toast-container">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          class={`toast ${toast.type} ${toast.type === 'error' ? 'toast-error' : 'toast-success'}`}
          onClick={() => onDismiss(toast.id)}
        >
          <span>{toast.message}</span>
          {toast.type === 'error' && <span class="toast-close">×</span>}
        </div>
      ))}
    </div>
  );
}
```

### 3.3 样式

```css
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
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  pointer-events: all;
  animation: toast-in 0.2s ease;
  max-width: 320px;
}
.toast-success {
  border-color: rgba(34, 197, 94, 0.4);
  color: #86efac;
}
.toast-error {
  border-color: rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  cursor: pointer;
}
.toast-close { margin-left: auto; cursor: pointer; }

@keyframes toast-in {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
```

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/hooks/useToast.js` | 新建：toast state + show/dismiss |
| `web/src/components/ToastContainer.jsx` | 新建：fixed-position toast 渲染 |
| `web/src/app.jsx` | ToastContainer 渲染，替换 alert()，各操作添加 toast |
| `web/src/lib/i18n.js` | 新增 toast 相关翻译 key |

## 5. i18n Key

| Key | ZH | EN |
|-----|----|----|
| toast_published | ✓ 职位已发布到 Nostr！ | ✓ Job posted to Nostr! |
| toast_deleted | ✓ 职位已删除 | ✓ Job deleted |
| toast_edited | ✓ 职位已更新 | ✓ Job updated |
| toast_delete_err | ✗ 删除失败，请重试 | ✗ Failed to delete, please try again |
| toast_nip07_err | 请先安装 NIP-07 扩展来使用此功能 | Please install a NIP-07 extension to use this feature |

## 6. 验收标准

- [ ] `alert()` 不再出现在 app 代码中
- [ ] 发布成功显示 toast
- [ ] 删除成功显示 toast
- [ ] 编辑成功显示 toast
- [ ] 错误显示 toast（需手动关闭）
- [ ] Toast 自动消失（成功 3s 后）
- [ ] 多个 toast 正确堆叠
- [ ] 现有测试全部通过
