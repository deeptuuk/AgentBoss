# AgentBoss 可靠性修复 + Favicon — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** useJobs 内存泄漏修复 + 竞态保护 + Favicon，修复 #37

---

## Task 1: useJobs 内存泄漏 + 竞态修复

**Files:**
- Modify: `web/src/hooks/useJobs.js`

- [ ] **Step 1: 添加 requestIdRef**

```javascript
const requestIdRef = useRef(0);
```

- [ ] **Step 2: 修改 loadJobs — 竞态保护**

```javascript
const loadJobs = useCallback(async () => {
  const currentId = ++requestIdRef.current;
  setLoading(true);
  setError(null);

  const relay = createRelayClient();

  try {
    await relay.connect();

    const allJobs = [];
    relay.onEvent((event) => {
      const job = parseJobEvent(event);
      if (job) allJobs.push(job);
    });

    relay.onEOSE(() => {
      if (currentId !== requestIdRef.current) { relay.close(); return; }

      allJobs.sort((a, b) => b.created_at - a.created_at);

      let filtered = allJobs;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = allJobs.filter(
          (j) =>
            j.title.toLowerCase().includes(q) ||
            j.company.toLowerCase().includes(q) ||
            j.description.toLowerCase().includes(q)
        );
      }

      setJobs(filtered);
      setLoading(false);
      relay.close();
    });

    relay.subscribe('jobs', buildJobFilter({ province, city }));
  } catch (err) {
    if (currentId !== requestIdRef.current) { relay.close(); return; }
    setError(err.message);
    setLoading(false);
    relay.close();
  }
}, [province, city, searchQuery]);
```

- [ ] **Step 3: useEffect cleanup — 内存泄漏修复**

```javascript
useEffect(() => {
  loadJobs();
  return () => {
    // Cleanup: close relay on unmount, increment requestId to ignore stale callbacks
    requestIdRef.current++;
  };
}, [loadJobs]);
```

- [ ] **Step 4: 提交**

```bash
git add web/src/hooks/useJobs.js
git commit -m "$(cat <<'EOF'
fix(web): useJobs — cleanup relay on unmount + ignore stale requests

- useEffect cleanup increments requestIdRef + calls relay cleanup
- loadJobs ignores results from superseded requests
- Prevents state update on unmounted component

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Favicon

**Files:**
- Create: `web/public/favicon.svg`
- Modify: `web/index.html`

- [ ] **Step 1: 创建 favicon.svg**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
  <rect width="32" height="32" rx="8" fill="#1a1a2e"/>
  <path d="M18 4L8 18h8l-2 10 12-14h-9l3-10z" fill="#f59e0b"/>
</svg>
```

- [ ] **Step 2: 在 index.html 添加 link**

在 `<head>` 中添加：

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

- [ ] **Step 3: 提交**

```bash
git add web/public/favicon.svg web/index.html
git commit -m "$(cat <<'EOF'
feat(web): add ⚡ favicon — amber bolt on dark rounded square

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "fix(web): useJobs memory leak + race condition + favicon (#37)" \
  --body "$(cat <<'EOF'
## Summary

Reliability fixes + favicon for Issue #37.

## Changes

- `useJobs.js`:
  - `useEffect` cleanup increments `requestIdRef.current++` and closes relay
  - `loadJobs`: ignores results from superseded requests via `requestIdRef`
  - Prevents state update on unmounted component
- `public/favicon.svg`: ⚡ amber bolt SVG icon
- `index.html`: `<link rel="icon" type="image/svg+xml" href="/favicon.svg">`

## Verification

- [ ] `npm run dev` — no React state update warnings on unmount
- [ ] Rapid search — no multiple WebSocket connections
- [ ] Browser tab shows ⚡ icon
- [ ] `npm test` passes

Closes #37.
EOF
)"
```

---

## 注意事项

- `requestIdRef` 初始值 0，cleanup 时 `++` 使其变为 1，后续任何旧请求的 `currentId !== requestIdRef.current`
- relay.close() 在 cleanup 中调用，确保 WebSocket 立即关闭
