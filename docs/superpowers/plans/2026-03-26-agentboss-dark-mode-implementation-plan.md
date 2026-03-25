# AgentBoss Dark Mode Toggle — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 主题切换按钮 + CSS 变量覆盖 + 闪屏防护，修复 #46

---

## Task 1: index.html — 闪屏防护脚本

**Files:**
- Modify: `web/index.html`

- [ ] **Step 1: 在 `<head>` 最前面添加内联 script**

在 `<head>` 开头（`<meta charset>` 之后）添加：

```html
<script>
  (function() {
    const stored = localStorage.getItem('agentboss_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = stored ? stored === 'dark' : prefersDark;
    if (isDark) document.documentElement.classList.add('dark');
  })();
</script>
```

确保在 `<script type="module">`（Vite entry）之前。

- [ ] **Step 2: 提交**

```bash
git add web/index.html
git commit -m "$(cat <<'EOF'
feat(web): index.html — dark mode flash prevention inline script

Reads localStorage before JS bundle, sets .dark class synchronously.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: CSS — .dark 变量覆盖

**Files:**
- Modify: `web/src/styles/index.css`

- [ ] **Step 1: 在 CSS 末尾添加 .dark 变量**

```css
/* ── Dark Mode ─────────────────────────── */
.dark {
  --bg-primary: #0f0f1a;
  --bg-secondary: #1a1a2e;
  --bg-tertiary: #16213e;
  --text: #e0e0e0;
  --text-muted: #9ca3af;
  --accent: #f59e0b;
  --accent-hover: #fbbf24;
  --accent-border: rgba(245, 158, 11, 0.3);
  --border: rgba(255, 255, 255, 0.1);
  --surface: #1a1a2e;
  --surface-hover: #232340;
}

/* Smooth theme transition */
:root {
  transition: background-color 0.3s, color 0.3s;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add .dark CSS variables — dark mode color overrides

Overrides all CSS custom properties for dark theme.
Smooth 0.3s transition on theme switch.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: ThemeToggle 组件

**Files:**
- Create: `web/src/components/ThemeToggle.jsx`

- [ ] **Step 1: 实现组件**

```jsx
import { useState } from 'preact/hooks';

const STORAGE_KEY = 'agentboss_theme';

function isDark() {
  return document.documentElement.classList.contains('dark');
}

export function ThemeToggle() {
  const [dark, setDark] = useState(() => isDark());

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem(STORAGE_KEY, next ? 'dark' : 'light');
  };

  return (
    <button
      class="theme-toggle"
      onClick={toggle}
      title={dark ? 'Light mode' : 'Dark mode'}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {dark ? '☀️' : '🌙'}
    </button>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/ThemeToggle.jsx
git commit -m "$(cat <<'EOF'
feat(web): add ThemeToggle — dark/light mode switch button

Reads current state from DOM class, persists to localStorage.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Navbar 集成 ThemeToggle

**Files:**
- Modify: `web/src/components/Navbar.jsx`

- [ ] **Step 1: 导入并添加 ThemeToggle**

在 LanguageSwitch 旁边添加：

```jsx
import { ThemeToggle } from './ThemeToggle.jsx';

// 在 navbar-actions 中，LanguageSwitch 之后添加：
<ThemeToggle />
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/Navbar.jsx
git commit -m "$(cat <<'EOF'
feat(web): Navbar — add ThemeToggle next to LanguageSwitch

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: ThemeToggle 样式

**Files:**
- Modify: `web/src/styles/index.css`

- [ ] **Step 1: 添加按钮样式**

```css
/* Theme Toggle */
.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
  line-height: 1;
}
.theme-toggle:hover {
  background: rgba(128, 128, 128, 0.15);
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add .theme-toggle styles — emoji button, hover state

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): dark mode toggle — system preference default, no flash (#46)" \
  --body "$(cat <<'EOF'
## Summary

Dark mode toggle with system preference default and no-flash loading.

## Changes

- `index.html`: inline `<script>` in `<head>` — sets `.dark` class before JS bundle, prevents flash
- `index.css`: `.dark` CSS variables override + smooth 0.3s transition
- `ThemeToggle.jsx`: ☀️/🌙 toggle button, reads/writes `agentboss_theme` localStorage
- `Navbar.jsx`: ThemeToggle integrated next to LanguageSwitch
- `index.css`: `.theme-toggle` button styles

## Verification

- [ ] Theme toggle button visible in Navbar
- [ ] Clicking toggles between light and dark theme
- [ ] Theme persists after page refresh
- [ ] No flash on page load (inline script runs before JS bundle)
- [ ] All components adapt to theme variables
- [ ] `npm test` passes

Closes #46.
EOF
)"
```

---

## 注意事项

- 内联 script 必须在 `<script type="module">` 之前，否则无法防止闪屏
- `isDark()` 读取 DOM class 而非 state，确保 SSR/同构场景兼容
- `localStorage` 的 `'agentboss_theme'` 值为 `'dark'` 或 `'light'` 字符串
- `toggle()` 同步调用 `document.documentElement.classList.toggle()`，state 更新是异步的但视觉切换无感知
