# AgentBoss Vercel 全量部署 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved

---

## 1. 背景

Issue #20：将 AgentBoss 全部部署（前端 + 文档）迁移到 Vercel。

当前状态：
- 前端：GitHub Pages（`/AgentBoss/`）
- 文档：GitHub Pages（`/AgentBoss/superpowers/`）
- 构建：Vite 输出到 `docs/`

## 2. 目标

- 将 Preact 前端部署到 Vercel（主站点）
- 将 docsify 文档也迁移到 Vercel（`/superpowers/` 路径）
- GitHub Pages 可保留（用于灾备）或后续废弃

## 3. 架构决策

### 部署模型

| 资产 | 托管平台 | URL |
|------|---------|-----|
| 前端（Vite 构建） | Vercel | `*.vercel.app/` |
| 文档（docsify） | Vercel | `*.vercel.app/superpowers/` |

### docsify 打包策略

Vite 构建后，通过自定义插件将 `docs/superpowers/` 复制到 `dist/superpowers/`：

```javascript
// web/vite.config.js
import { copyFileSync, mkdirSync, readdirSync, statSync } from 'fs';
import { resolve, join } from 'path';

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
      console.log('docsify copied to dist/superpowers/');
    },
  };
}
```

### Vite 配置变更

当前 `web/vite.config.js`：
```javascript
base: '/AgentBoss/',
build: {
  outDir: resolve(__dirname, '../docs'),
  emptyOutDir: false,  // PR #21 移除
},
```

更新后：
```javascript
// web/vite.config.js
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';
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

### docsify 路径变更

| 环境 | 文档 URL |
|------|---------|
| GitHub Pages（历史） | `/AgentBoss/superpowers/` |
| Vercel（本次） | `/superpowers/` |

**docsify 配置无需变更：** `relativePath: true` 使 docsify 自动适配任意 base path。

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/vite.config.js` | 环境变量驱动 base/outDir + docsifyCopyPlugin() |
| `web/vercel.json` | 新增：Vercel 构建配置 |

## 5. Vercel 配置

```json
{
  "buildCommand": "npm install && npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite"
}
```

Vercel Dashboard 环境变量：`VITE_BASE_PATH=/`

## 6. 验证标准

- [ ] Vercel 部署成功，`dist/index.html` 可访问
- [ ] 文档 `dist/superpowers/index.html` 存在
- [ ] 前端资源路径正确（无 404）
- [ ] Nostr relay 连接正常（职位列表可加载）
- [ ] 文档 `/superpowers/` 可正常浏览

## 7. 风险与回滚

- **风险：** docsify 文件未正确复制到 dist
- **回滚：** GitHub Pages 仍可访问（原始文件在 `docs/superpowers/`）
- **GitHub Pages 处理：** 本次不废弃，保留作为备用

## 8. 不在本次范围

- 自定义域名
- Vercel API Routes / 后端服务
- 数据库集成
- GitHub Pages 废弃
