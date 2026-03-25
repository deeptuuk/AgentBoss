# AgentBoss 文档站点部署到 GitHub Pages — 设计文档

## 背景

Issue #16 "把网页上线github" 务实的落地方式是部署静态文档到 GitHub Pages，让项目有公开可访问的在线内容。

当前 `web/` 是 FastAPI Python 应用，无法直接部署到 GitHub Pages（仅支持静态站点）。最快方案：使用 docsify 将 `docs/` 目录托管为静态文档站点。

## 方案选择

**docsify（推荐）**
- 零配置静态文档工具，直接读取 markdown 文件
- 只需创建 `docs/index.html`（加载 docsify CDN）
- 无需 pip 依赖，GitHub Pages 直接托管
- 保留现有 `docs/superpowers/specs/` 等 markdown 文件

## 变更内容

### 文件 1：`docs/index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentBoss</title>
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify/lib/themes/buble.css">
</head>
<body>
  <div id="app"></div>
  <script>
    window.$docsify = {
      name: 'AgentBoss',
      repo: 'https://github.com/nicholasyangyang/AgentBoss',
      loadSidebar: true,
      subMaxLevel: 3,
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/docsify.min.js"></script>
</body>
</html>
```

### 文件 2：`docs/.nojekyll`

空文件，防止 GitHub Pages 对以下划线开头的文件跳过处理（docsify 内部使用 `_` 前缀文件）。

### 文件 3：`docs/_sidebar.md`

```markdown
- [首页](README)
- [English](https://github.com/nicholasyangyang/AgentBoss#readme)

## 规格文档
[规格文档索引](specs/)
```

### GitHub Pages 启用

Settings → Pages → Source: "Deploy from a branch" → Branch: `master` / `/docs`

> 注意：GitHub Pages 从 `master/docs` 目录托管，URL：`https://nicholasyangyang.github.io/AgentBoss/`

## 设计原则

- **最小化变更**：仅添加 3 个静态文件
- **零依赖**：docsify 通过 CDN 加载，无需 npm/pip
- **保留现有内容**：所有 markdown 文件无需迁移
- **无需 CI/CD**：GitHub Pages 直接托管

## 相关文件

- `docs/index.html` — 新增
- `docs/.nojekyll` — 新增
- `docs/_sidebar.md` — 新增
