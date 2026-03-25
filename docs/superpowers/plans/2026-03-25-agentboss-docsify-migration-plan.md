# AgentBoss docsify 子目录迁移 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 docsify 迁移到 `docs/superpowers/` 子目录，与 Vite 构建输出（`docs/`）分离。

**当前状态：** `docs/index.html` 已是 Vite 前端入口，`docs/superpowers/` 含规格文档但无 docsify 入口。

---

## 文件变更概览

| 文件 | 变更类型 |
|------|---------|
| `docs/superpowers/index.html` | 新增：docsify 入口 |
| `docs/superpowers/_sidebar.md` | 新增：导航侧边栏 |
| `docs/index.html` | 已确认：Vite 前端入口（保持不变） |

---

## Task 1: 创建 docsify 子目录入口

**Files:**
- Create: `docs/superpowers/index.html`

- [ ] **Step 1: 创建 `docs/superpowers/index.html`**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentBoss - 规格文档</title>
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify/lib/themes/buble.css">
</head>
<body>
  <div id="app">加载中...</div>
  <script>
    window.$docsify = {
      name: 'AgentBoss 规格',
      repo: 'https://github.com/nicholasyangyang/AgentBoss',
      loadSidebar: '_sidebar.md',
      subMaxLevel: 3,
      relativePath: true,
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/docsify.min.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 `docs/superpowers/_sidebar.md`**

```markdown
<!-- docs/superpowers/_sidebar.md -->

* [规格文档](/)
  * [AgentBoss 静态前端设计](./specs/2026-03-25-agentboss-static-frontend-design.md)
```

- [ ] **Step 3: 提交**

```bash
git add docs/superpowers/index.html docs/superpowers/_sidebar.md
git commit -m "$(cat <<'EOF'
feat(docs): add docsify entry point in docs/superpowers/

docsify now runs from docs/superpowers/ subdirectory,
separate from Vite output in docs/ root.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: 推送并提 PR**

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(docs): docsify subdirectory migration" \
  --body "Move docsify to docs/superpowers/ subdirectory to avoid Vite build conflict."
```

---

## 验证

合并后访问：
- 前端：https://nicholasyangyang.github.io/AgentBoss/
- 文档：https://nicholasyangyang.github.io/AgentBoss/superpowers/

两者均返回 200 即完成。

---

## 相关文件

- `docs/index.html` — Vite 前端入口（不变）
- `docs/superpowers/` — docsify 文档（迁移后）
