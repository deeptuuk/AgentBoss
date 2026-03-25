# AgentBoss Vercel 全量部署 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修改 Vite 配置支持多平台部署，创建 vercel.json，将 docsify 文档打包进 Vercel 构建输出。

---

## Task 1: 修改 vite.config.js

**Files:**
- Modify: `web/vite.config.js`

- [ ] **Step 1: 写入更新后的 vite.config.js**

```javascript
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve, join } from 'path';
import { copyFileSync, mkdirSync, readdirSync, statSync } from 'fs';

const isVercel = process.env.VITE_BASE_PATH === '/';

function copyDir(src, dest) {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    statSync(srcPath).isDirectory()
      ? copyDir(srcPath, destPath)
      : copyFileSync(srcPath, destPath);
  }
}

function docsifyCopyPlugin() {
  return {
    name: 'docsify-copy',
    closeBundle() {
      const src = resolve(__dirname, '../docs/superpowers');
      const dest = resolve(__dirname, 'dist/superpowers');
      copyDir(src, dest);
      console.log('[docsify-copy] copied to dist/superpowers/');
    },
  };
}

export default defineConfig({
  plugins: [preact(), docsifyCopyPlugin()],
  base: process.env.VITE_BASE_PATH || '/',
  build: {
    outDir: isVercel ? 'dist' : resolve(__dirname, '../docs'),
    emptyOutDir: true,
  },
  server: { port: 3000, open: true },
});
```

- [ ] **Step 2: 本地验证构建（Vercel 模式）**

```bash
cd /home/deeptuuk/Code4/AgentBoss/web
VITE_BASE_PATH=/ npm run build
ls dist/
ls dist/superpowers/
# 预期：dist/index.html + dist/assets/ + dist/superpowers/index.html
```

- [ ] **Step 3: 验证 docsify 文档结构**

```bash
ls dist/superpowers/
# 预期：index.html, _sidebar.md, specs/
```

- [ ] **Step 4: 提交**

```bash
cd /home/deeptuuk/Code4/AgentBoss
git add web/vite.config.js
git commit -m "$(cat <<'EOF'
feat(web): env-driven multi-platform Vite config with docsify bundling

- VITE_BASE_PATH=/ -> Vercel (dist/, base /)
- VITE_BASE_PATH=/AgentBoss/ -> GitHub Pages (../docs/, base /AgentBoss/)
- docsifyCopyPlugin() copies docs/superpowers/ to dist/superpowers/ post-build
- emptyOutDir: true

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 创建 vercel.json

**Files:**
- Create: `web/vercel.json`

- [ ] **Step 1: 创建 web/vercel.json**

```json
{
  "buildCommand": "npm install && npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite"
}
```

- [ ] **Step 2: 提交**

```bash
git add web/vercel.json
git commit -m "$(cat <<'EOF'
feat(web): add Vercel deployment configuration

- Build: npm install && npm run build
- Output: dist/
- Framework: vite

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
  --title "feat(web): Vercel deployment — env-driven config + docsify bundling" \
  --body "$(cat <<'EOF'
## Summary

Enable full Vercel deployment: Preact frontend + docsify docs, all served from `dist/`.

## Changes

- `web/vite.config.js`:
  - `docsifyCopyPlugin()` copies `docs/superpowers/` → `dist/superpowers/` after build
  - `base` and `outDir` driven by `VITE_BASE_PATH` env var
  - `emptyOutDir: true`
- `web/vercel.json`: Vercel build + output config

## URLs After Deploy

- Frontend: `*.vercel.app/`
- Docs: `*.vercel.app/superpowers/`

## Vercel Setup

1. Import `nicholasyangyang/AgentBoss` on vercel.com
2. Root Directory: `web/`
3. Environment Variable: `VITE_BASE_PATH` = `/`
4. Deploy

## Verification

- [x] `VITE_BASE_PATH=/ npm run build` succeeds
- [x] `dist/index.html` exists (frontend)
- [x] `dist/superpowers/index.html` exists (docsify)

Closes #20.
EOF
)"
```

---

## 注意事项

- `docs/superpowers/` 已在 git 中，无需额外文件
- docsify `relativePath: true` 自动适配 base path，无需修改
- GitHub Pages 保留作为备用，不影响本次部署
