# AgentBoss Dark Mode Toggle — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-26
**Status:** Approved
**Issue:** #46

---

## 1. 背景

AgentBoss 当前无主题切换。Nostr 用户普遍偏好深色模式。通过 CSS 变量覆盖（`.dark` class）实现，无需重构现有样式。

## 2. 设计决策

- **默认跟随系统偏好**（`prefers-color-scheme: dark`），减少手动配置
- **只定义 `.dark` override**，浅色是当前默认，无需重复定义
- **闪屏防护**：在 `index.html` `<head>` 加内联 script，JS bundle 加载前设置 class

## 3. 技术方案

### 3.1 index.html — 闪屏防护

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

### 3.2 CSS — .dark 变量覆盖

在 `index.css` 末尾添加 `.dark` class，覆盖关键颜色变量：

```css
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
```

### 3.3 ThemeToggle 组件

```jsx
// web/src/components/ThemeToggle.jsx

import { useState, useEffect } from 'preact/hooks';

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
    <button class="theme-toggle" onClick={toggle} title={dark ? 'Switch to light' : 'Switch to dark'}>
      {dark ? '☀️' : '🌙'}
    </button>
  );
}
```

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/index.html` | `<head>` 内联 script，闪屏防护 |
| `web/src/styles/index.css` | `.dark` 变量覆盖 |
| `web/src/components/ThemeToggle.jsx` | 新建：主题切换按钮 |
| `web/src/components/Navbar.jsx` | 集成 ThemeToggle |
| `web/src/lib/i18n.js` | 主题相关翻译 key（可选） |

## 5. i18n（可选）

| Key | ZH | EN |
|-----|----|----|
| theme_light | 浅色模式 | Light |
| theme_dark | 深色模式 | Dark |

## 6. 验收标准

- [ ] 主题切换按钮在 Navbar 区域显示（LanguageSwitch 附近）
- [ ] 点击切换深色/浅色主题
- [ ] 刷新后主题保持（localStorage 持久化）
- [ ] 页面加载无闪屏（内联 script 先于 JS bundle）
- [ ] 所有组件颜色随主题变量变化
- [ ] 现有测试全部通过
