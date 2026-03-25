# AgentBoss Vercel 部署实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修改 `web/vite.config.js` 支持环境变量驱动的 base path，创建 `web/vercel.json` 配置 Vercel 构建。

**Architecture:** Vite 通过 `VITE_BASE_PATH` 环境变量切换输出目录：Vercel（`base: '/'`, `outDir: 'dist'`）vs GitHub Pages（`base: '/AgentBoss/'`, `outDir: '../docs'`）。

---

## Task 1: 修改 vite.config.js

**Files:**
- Modify: `web/vite.config.js`

- [ ] **Step 1: 读取当前 vite.config.js**

当前 `web/vite.config.js` 内容（PR #21 合并后）：
```javascript
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [preact()],
  // Deploy to /AgentBoss/ subdirectory on GitHub Pages
  base: '/AgentBoss/',
  build: {
    outDir: resolve(__dirname, '../docs'),
  },
  server: {
    port: 3000,
    open: true,
  },
});
```

- [ ] **Step 2: 写入更新后的 vite.config.js**

```javascript
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';

const isVercel = process.env.VITE_BASE_PATH === '/';

export default defineConfig({
  plugins: [preact()],
  // base path: Vercel='/', GitHub Pages='/AgentBoss/'
  base: process.env.VITE_BASE_PATH || '/',
  build: {
    // outDir: Vercel uses 'dist/', GitHub Pages uses '../docs'
    outDir: isVercel ? 'dist' : resolve(__dirname, '../docs'),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: true,
  },
});
```

- [ ] **Step 3: 本地验证构建（Vercel 模式）**

```bash
cd /home/deeptuuk/Code4/AgentBoss/web
VITE_BASE_PATH=/ npm run build
# 预期：dist/ 目录生成 index.html + assets/
ls dist/
```

- [ ] **Step 4: 本地验证构建（GitHub Pages 模式）**

```bash
VITE_BASE_PATH=/AgentBoss/ npm run build
# 预期：../docs/ 目录生成 index.html + assets/
ls ../docs/
```

- [ ] **Step 5: 提交**

```bash
cd /home/deeptuuk/Code4/AgentBoss
git add web/vite.config.js
git commit -m "$(cat <<'EOF'
feat(web): env-driven base path for multi-platform deployment

VITE_BASE_PATH=/ -> Vercel (dist/, base=/)
VITE_BASE_PATH=/AgentBoss/ -> GitHub Pages (../docs/, base=/AgentBoss/)
emptyOutDir: true added.

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
feat(web): add Vercel deployment config

vercel.json configures:
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
  --title "feat(web): Vercel deployment — env-driven base path + vercel.json" \
  --body "$(cat <<'EOF'
## Summary

Enable Vercel deployment via env-driven Vite config and vercel.json.

## Changes

- `web/vite.config.js`: `base` and `outDir` now driven by `VITE_BASE_PATH` env var
  - `VITE_BASE_PATH=/` → Vercel (`dist/`, base `/`)
  - `VITE_BASE_PATH=/AgentBoss/` → GitHub Pages (`../docs/`, base `/AgentBoss/`)
- `web/vercel.json`: Vercel build configuration

## Vercel Setup

1. Import `nicholasyangyang/AgentBoss` on vercel.com
2. Set Root Directory to `web/`
3. Add Environment Variable: `VITE_BASE_PATH` = `/`
4. Deploy

## Verification

- [x] `VITE_BASE_PATH=/ npm run build` → `dist/` output
- [x] `VITE_BASE_PATH=/AgentBoss/ npm run build` → `../docs/` output

Closes #20.
EOF
)"
```

---

## 注意事项

- Vercel Dashboard 需要手动设置环境变量 `VITE_BASE_PATH=/`
- 推送前 deeptuuk 先 `git pull` 同步最新代码
- `emptyOutDir: true` 会清空目标目录，GitHub Pages 场景需注意
