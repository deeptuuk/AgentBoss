# AgentBoss 静态前端 GitHub Pages 部署 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Preact 前端构建输出到 `docs/` 目录，使 GitHub Pages 从 `master/docs` 自动托管静态站点。

**当前状态：** UI 代码已实现（commit `bf079fb`），`web/` 目录含完整 Preact + Vite 前端，`vite.config.js` 已设置 `base: '/AgentBoss/'` 和 `outDir: 'dist'`。

---

## 文件变更概览

| 文件 | 变更类型 |
|------|---------|
| `web/vite.config.js` | 修改：output 到 `../docs` |
| 无新增文件 | |

---

## Task 1: 修改 Vite 配置，输出到 docs/ 目录

**Files:**
- Modify: `web/vite.config.js`

- [ ] **Step 1: 修改 `vite.config.js` 的 outDir**

将构建输出从 `web/dist/` 改为 `docs/`（仓库根目录），使 GitHub Pages 能直接从 `master/docs` 托管：

```javascript
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [preact()],
  base: '/AgentBoss/',
  build: {
    outDir: resolve(__dirname, '../docs'),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: true,
  },
});
```

> 注意：`resolve(__dirname, '../docs')` 将输出到仓库根目录的 `docs/` 文件夹。

- [ ] **Step 2: 运行构建验证**

```bash
cd /home/deeptuuk/Code4/AgentBoss/web
npm install
npm run build
```

预期：构建成功，`docs/` 目录生成 `index.html` 和 `assets/` 目录。

验证：
```bash
ls /home/deeptuuk/Code3/AgentBoss/docs/
ls /home/deeptuuk/Code3/AgentBoss/docs/assets/
```

预期：`docs/index.html` 和 `docs/assets/` 存在。

- [ ] **Step 3: 提交**

```bash
cd /home/deeptuuk/Code4/AgentBoss
git add web/vite.config.js
git commit -m "$(cat <<'EOF'
feat(web): output build to docs/ for GitHub Pages deployment

Build output redirected from web/dist/ to docs/ (repo root),
enabling GitHub Pages to serve from master/docs branch.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: 推送到 deeptuuk fork 并提 PR**

```bash
# 推送到 deeptuuk fork（确认 remote 已配置）
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat: GitHub Pages deployment — build output to docs/" \
  --body "$(cat <<'EOF'
## Summary

Redirect Vite build output to `docs/` for GitHub Pages deployment from `master/docs`.

## Changes

- `web/vite.config.js`: `outDir` changed from `dist/` to `../docs` (repo root `docs/`)

## Verification

- [x] `npm run build` succeeds
- [x] `docs/index.html` generated
- [x] `docs/assets/` contains JS/CSS bundles

## After Merge

GitHub Pages will automatically serve the static site from `master/docs`.

Closes #18.
EOF
)"
```

- [ ] **Step 5: 通知 nicholasyangyang 审核 PR**

---

## Task 2: PR 审核后验证 GitHub Pages

- [ ] **Step 1: PR 合并后，等待 GitHub Pages 构建（通常 1-2 分钟）**

- [ ] **Step 2: 访问 https://nicholasyangyang.github.io/AgentBoss/ 验证**

- [ ] **Step 3: 检查网络请求确认 assets 路径正确**

预期：
- `index.html` → 200
- `assets/index-*.js` → 200
- `assets/index-*.css` → 200

---

## 注意事项

- `docs/` 目录已存在（docsify 文档站点），Vite 构建会覆盖 `index.html`，但不会影响 `docs/superpowers/` 等子目录
- `docs/README.md`、`docs/.nojekyll`、`docs/_sidebar.md` 不会被构建覆盖
- GitHub Pages 设置已启用（来自之前的部署），无需重新配置

## 相关文件

- `web/vite.config.js` — Vite 构建配置
- `web/src/` — 源代码
- `docs/` — GitHub Pages 托管目录
- Issue: https://github.com/nicholasyangyang/AgentBoss/issues/18
