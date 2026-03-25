# AgentBoss 可靠性修复 + Favicon — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved
**Issue:** #37

---

## 1. 背景

两个生产级可靠性 bug + 一个简单品牌问题。

## 2. 问题详解

### 问题 1: useJobs 内存泄漏

`useJobs` 中的 relay 实例在 `onEOSE` 回调中持有对组件 state 的引用，组件 unmount 后回调仍可能被触发。

**修复：** 在 `useEffect` cleanup 中调用 `relay.close()`，确保回调不再触发。

### 问题 2: useJobs 并发竞态

`loadJobs` 每次调用创建新 WebSocket。快速搜索时多个调用并发执行，结果互相覆盖。

**修复：** 使用 `useRef` 跟踪 `requestId`，只处理最新请求的结果。

```javascript
const requestIdRef = useRef(0);

const loadJobs = useCallback(async () => {
  const currentId = ++requestIdRef.current;
  // ...
  relay.onEOSE(() => {
    if (currentId !== requestIdRef.current) return; // ignore stale
    // ...
  });
});
```

### 问题 3: Favicon

**修复：** 创建 `web/public/favicon.svg`，在 `index.html` 添加 `<link rel="icon">`。

## 3. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/hooks/useJobs.js` | cleanup 关闭 relay + requestIdRef 竞态保护 |
| `web/public/favicon.svg` | 新增 ⚡ 闪电图标 SVG |
| `web/index.html` | 添加 favicon link |

## 4. 验证标准

- [ ] `npm run dev` 无 React state warning
- [ ] 快速搜索无多个 WebSocket
- [ ] 浏览器标签页显示 ⚡ 图标
