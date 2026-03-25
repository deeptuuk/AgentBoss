# AgentBoss 文档站点部署到 GitHub Pages — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建 docsify 静态文档站点，部署到 GitHub Pages，让项目有公开可访问的在线文档。

**Architecture:** 零配置 docsify + GitHub Pages 直接托管，无需 CI/CD。

---

## 文件变更概览

| 文件 | 变更类型 |
|------|---------|
| `docs/index.html` | 新增 |
| `docs/.nojekyll` | 新增 |
| `docs/_sidebar.md` | 新增 |

---

## Task 1: 创建 docsify 静态文件

**Files:**
- Create: `docs/index.html`
- Create: `docs/.nojekyll`
- Create: `docs/_sidebar.md`

- [ ] **Step 1: 创建 `docs/index.html`**

```bash
cat > docs/index.html << 'EOF'
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
EOF
```

- [ ] **Step 2: 创建 `docs/.nojekyll`**

```bash
touch docs/.nojekyll
```

- [ ] **Step 3: 创建 `docs/_sidebar.md`**

```bash
cat > docs/_sidebar.md << 'EOF'
- [首页](README)
- [English](https://github.com/nicholasyangyang/AgentBoss#readme)

## 规格文档
[规格文档索引](specs/)
EOF
```

- [ ] **Step 4: 验证文件存在**

```bash
ls -la docs/index.html docs/.nojekyll docs/_sidebar.md
```

- [ ] **Step 5: 提交**

```bash
git add docs/index.html docs/.nojekyll docs/_sidebar.md
git commit -m "$(cat <<'EOF'
feat(docs): add docsify static documentation site for GitHub Pages

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: 推送到 deeptuuk fork**

```bash
git push
```

---

## Task 2: 提 PR 并通知

- [ ] **Step 1: 从 deeptuuk fork 提 PR**

```bash
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(docs): add docsify site for GitHub Pages" \
  --body "$(cat <<'EOF'
Deploy static documentation site to GitHub Pages using docsify.

Files added:
- `docs/index.html` — docsify entry point
- `docs/.nojekyll` — prevent GitHub from ignoring underscore files
- `docs/_sidebar.md` — navigation sidebar

After merge: Settings → Pages → Source: master /docs

Closes #16.
EOF
)"
```

- [ ] **Step 2: 通知 nicholasyangyang（npub1l4ae04...）审核**

---

## GitHub Pages 启用步骤（合并后手动操作）

1. 进入仓库 Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `master` / `/docs`
4. Save

访问：`https://nicholasyangyang.github.io/AgentBoss/`

---

## 相关文件

- Spec: `docs/superpowers/specs/2026-03-25-agentboss-github-pages-deploy-design.md`
- Issue: https://github.com/nicholasyangyang/AgentBoss/issues/16
