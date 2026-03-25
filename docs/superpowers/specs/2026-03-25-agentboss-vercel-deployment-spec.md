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
```

Vercel 部署需要调整为：
```javascript
base: '/',  // Vercel 根路径
```

### 构建配置

- `web/` 作为 Vercel 项目根目录
- Build Command: `npm install && npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

### 多平台共存策略

**问题：** `base: '/AgentBoss/'` 是硬编码的，GitHub Pages 和 Vercel 需要不同值。

**解决方案：** 使用环境变量动态配置 base path。

```javascript
// web/vite.config.js
export default defineConfig({
  plugins: [preact()],
  base: process.env.VITE_BASE_PATH || '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  // ...
});
```

Vercel 项目环境变量设置：
- `VITE_BASE_PATH=/`（Vercel 部署）

GitHub Pages 构建（如需回滚）：
- `VITE_BASE_PATH=/AgentBoss/`

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
| `web/vite.config.js` | `base` 改为 `process.env.VITE_BASE_PATH \|\| '/'` |
| `vercel.json` | 新增：Vercel 构建配置 |
| `web/src/lib/relay.js` | 无变更（relay URL 不涉及 base path） |
| `.github/workflows/deploy.yml` | 可选移除（前端改由 Vercel 管理） |

## 6. 实施步骤

1. 创建 `web/vercel.json`
2. 修改 `web/vite.config.js` base path 为环境变量
3. Vercel Dashboard 添加环境变量 `VITE_BASE_PATH=/`
4. Vercel 导入 `nicholasyangyang/AgentBoss` 仓库，Root Directory 设为 `web/`
5. 验证部署
6. 更新 `web/vite.config.js` 的 GitHub Pages 注释

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
