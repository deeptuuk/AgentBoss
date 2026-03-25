# AgentBoss My Jobs View + Edit — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-26
**Status:** Approved
**Issue:** #42

---

## 1. 背景

Issue #39 实现删除功能后，用户无法查看和管理自己发布的职位。补充 My Jobs 视图和编辑功能。

## 2. 功能概述

### My Jobs 视图
- Navbar 新增「我的职位」tab（仅 NIP-07 已连接时显示）
- 展示当前用户发布的职位（`job.pubkey === currentUserPubkey`）
- 空状态："你还没有发布过职位" + CTA 按钮
- 发布成功后不清除当前视图

### 编辑职位
- My Jobs 列表每条职位显示「编辑」按钮
- 点击打开预填好的 PublishForm（字段已填充）
- 用户修改后确认：自动删除旧帖 + 发布新帖（原子性由前端控制）
- MVP 不显示 loading 状态

## 3. 技术方案

### 3.1 视图状态

```jsx
const [view, setView] = useState('all'); // 'all' | 'mine'

// Navbar: tab switch
{hasSigner && (
  <button
    class={view === 'mine' ? 'tab-active' : 'tab'}
    onClick={() => setView('mine')}
  >
    {t('my_jobs_tab')}
  </button>
)}

// Content: conditional render
{view === 'mine' ? (
  <JobList jobs={myJobs} showOnlyMine onEdit={handleEdit} />
) : (
  <JobList jobs={jobs} onDelete={...} />
)}
```

### 3.2 My Jobs 过滤

```jsx
const { pubkey } = useAuth();
const myJobs = jobs.filter((j) => j.pubkey === pubkey);
```

### 3.3 编辑流程

```
点击编辑 → setEditingJob(job) → PublishForm 打开（预填字段）
→ 用户修改 → handleEditSubmit → deleteJob(旧d_tag) → publishJob(新数据)
→ markDeleted(旧d_tag) → reload() → setEditingJob(null)
```

### 3.4 PublishForm 编辑模式

```jsx
export function PublishForm({ jobToEdit, onClose, onSuccess }) {
  // jobToEdit 存在时：预填表单，标题改为"编辑职位"
  const isEditing = !!jobToEdit;
  const [form, setForm] = useState({
    title: jobToEdit?.title || '',
    company: jobToEdit?.company || '',
    ...
  });

  const handleSubmit = async (e) => {
    if (isEditing) {
      // 1. 删除旧帖
      await deleteJob(jobToEdit.d_tag, pubkey);
      markDeleted(jobToEdit.d_tag);
    }
    // 2. 发布新帖
    await publishJob(form);
    onSuccess();
    onClose();
  };
}
```

### 3.5 侧边栏统计

```jsx
<div class="sidebar-widget">
  <div class="sidebar-title">{t('data_overview')}</div>
  <div class="stats-grid">
    <div class="stat-item">
      <div class="stat-value">{myJobs.length}</div>
      <div class="stat-label">{t('my_jobs')}</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">{favCount}</div>
      <div class="stat-label">{t('favorites')}</div>
    </div>
  </div>
</div>
```

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/app.jsx` | `view` state + myJobs 过滤 + 编辑流程 |
| `web/src/components/Navbar.jsx` | My Jobs tab（仅签名后显示） |
| `web/src/components/PublishForm.jsx` | `jobToEdit` prop → 预填 + 编辑提交逻辑 |
| `web/src/components/JobList.jsx` | `showOnlyMine` + `onEdit` props |
| `web/src/components/JobCard.jsx` | `onEdit` prop → 编辑按钮 |
| `web/src/lib/i18n.js` | my_jobs, my_jobs_tab, no_my_jobs, edit 等翻译 key |

## 5. 翻译 key

| Key | ZH | EN |
|-----|----|----|
| my_jobs_tab | 我的职位 | My Jobs |
| my_jobs | 我的职位 | My Jobs |
| no_my_jobs | 你还没有发布过职位 | You haven't posted any jobs yet |
| edit | 编辑 | Edit |
| edit_job | 编辑职位 | Edit Job |

## 6. 验收标准

- [ ] Navbar 仅 NIP-07 连接后显示「我的职位」tab
- [ ] My Jobs 列表仅显示当前用户发布的职位
- [ ] 空状态显示 CTA
- [ ] 点击编辑打开预填表单
- [ ] 编辑提交后旧帖删除、新帖发布
- [ ] 侧边栏显示我的职位数量
- [ ] 现有测试全部通过
