# AgentBoss Vercel 静态前端部署 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Draft

---

## 1. 背景

Issue #20：将 AgentBoss 前端部署到 Vercel，与 GitHub Pages（文档）并存。

当前状态：
- 前端：GitHub Pages（`/AgentBoss/`）
- 文档：GitHub Pages（`/AgentBoss/superpowers/`）
- 构建：Vite 输出到 `docs/`

## 2. 目标

- 将 Preact 前端部署到 Vercel 作为主站点
- 文档继续保留在 GitHub Pages（`/AgentBoss/superpowers/`）
- 两个托管平台完全独立

## 3. 架构决策

### 部署模型

| 资产 | 托管平台 | URL |
|------|---------|-----|
| 前端（Vite 构建） | Vercel | `*.vercel.app` 或自定义域名 |
| 文档（docsify） | GitHub Pages | `nicholasyangyang.github.io/AgentBoss/superpowers/` |

### Vite 配置变更

当前 `web/vite.config.js`：
```javascript
base: '/AgentBoss/',  // GitHub Pages 子目录路径
build: {
  outDir: resolve(__dirname, '../docs'),  // GitHub Pages docs/ 目录
  emptyOutDir: false,  // PR #21 移除，避免清空 docsify 文件
},
```

Vercel 部署需要同时调整 `base` 和 `outDir`：

```javascript
// web/vite.config.js
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';

const isVercel = process.env.VITE_BASE_PATH === '/';

export default defineConfig({
  plugins: [preact()],
  base: process.env.VITE_BASE_PATH || '/',
  build: {
    outDir: isVercel ? 'dist' : resolve(__dirname, '../docs'),
    emptyOutDir: true,  // 始终清空输出目录，避免残留文件
  },
  // ...
});
```

**`emptyOutDir` 说明：**
- Vercel (`dist/`): 无冲突，始终清空
- GitHub Pages (`docs/`): 清空 `docs/` 再写入，docsify 入口 `docs/superpowers/` 需在构建后恢复
- 迁移后 GitHub Pages 不再承载前端，GitHub Pages 仅保留 docsify docs，`emptyOutDir` 对 docsify 无影响

### 多平台输出目录

| 环境变量 | base | outDir | 用途 |
|---------|------|--------|------|
| `VITE_BASE_PATH=/` | `/` | `dist/` | Vercel 部署 |
| `VITE_BASE_PATH=/AgentBoss/` | `/AgentBoss/` | `../docs` | GitHub Pages 回滚 |

## 4. Vercel 项目配置

### vercel.json（推荐）或 Vercel Dashboard 配置

```json
{
  "buildCommand": "npm install && npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite"
}
```

### Alternative：修改 package.json

```json
{
  "scripts": {
    "vercel-build": "vite build"
  }
}
```

## 5. 文件变更

| 文件 | 变更 |
|------|------|
| `web/vite.config.js` | `base` 和 `outDir` 均改为环境变量驱动，`emptyOutDir: true` |
| `web/vercel.json` | 新增：Vercel 构建配置 |
| `.github/workflows/deploy.yml` | 可选移除（前端改由 Vercel 管理） |

## 6. 实施步骤

1. 创建 `web/vercel.json`
2. 修改 `web/vite.config.js`：
   - 添加 `import { resolve } from 'path'`
   - 添加 `const isVercel = process.env.VITE_BASE_PATH === '/'`
   - `base: process.env.VITE_BASE_PATH || '/'`
   - `outDir: isVercel ? 'dist' : resolve(__dirname, '../docs')`
   - `emptyOutDir: true`
3. Vercel Dashboard 添加环境变量 `VITE_BASE_PATH=/`
4. Vercel 导入 `nicholasyangyang/AgentBoss` 仓库，Root Directory 设为 `web/`
5. 验证部署：资源路径正确（无 404），Nostr relay 连接正常
6. 更新 `web/vite.config.js` 注释说明多平台配置

## 7. 验证标准

- [ ] Vercel 部署成功，`dist/index.html` 可访问
- [ ] 所有资源路径（JS/CSS）正确加载
- [ ] Nostr relay 连接正常（职位列表可加载）
- [ ] GitHub Pages 文档 `/AgentBoss/superpowers/` 不受影响

## 8. 风险与回滚

- **风险：** 环境变量配置错误导致路径 404
- **回滚：** 将 `VITE_BASE_PATH` 改回 `/AgentBoss/`，Vercel 重新部署
- **GitHub Pages 前端：** 可通过撤销 `.github/workflows/` 变更恢复

## 9. 不在本次范围

- 自定义域名配置（future issue）
- Vercel API Routes / 后端服务（future issue）
- 数据库集成（future issue）
