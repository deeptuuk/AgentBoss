# AgentBoss My Jobs View + Edit — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** My Jobs 视图 + 编辑功能，修复 #42

---

## Task 1: 添加翻译 key

**Files:**
- Modify: `web/src/lib/i18n.js`

- [ ] **Step 1: 添加 my_jobs 相关 key**

```javascript
// zh
my_jobs_tab: '我的职位',
my_jobs: '我的职位',
no_my_jobs: '你还没有发布过职位',
edit: '编辑',
edit_job: '编辑职位',

// en
my_jobs_tab: 'My Jobs',
my_jobs: 'My Jobs',
no_my_jobs: "You haven't posted any jobs yet",
edit: 'Edit',
edit_job: 'Edit Job',
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/i18n.js
git commit -m "$(cat <<'EOF'
feat(web): add my_jobs + edit i18n keys

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: PublishForm 编辑模式

**Files:**
- Modify: `web/src/components/PublishForm.jsx`

- [ ] **Step 1: 添加 jobToEdit prop**

```jsx
export function PublishForm({ jobToEdit, onClose, onSuccess }) {
  const isEditing = !!jobToEdit;

  const [form, setForm] = useState({
    title: jobToEdit?.title || '',
    company: jobToEdit?.company || '',
    salary: jobToEdit?.salary || '',
    province: jobToEdit?.province || '',
    city: jobToEdit?.city || '',
    description: jobToEdit?.description || '',
    contact: jobToEdit?.contact || '',
  });
```

- [ ] **Step 2: 修改表单标题**

```jsx
<h2 class="modal-title" id="publish-title">
  {isEditing ? t('edit_job') : t('form_title')}
</h2>
```

- [ ] **Step 3: 修改 handleSubmit — 编辑时先删除旧帖**

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  setError(null);

  if (!form.title.trim()) return setError(t('err_title'));
  if (!form.company.trim()) return setError(t('err_company'));
  if (!form.province.trim()) return setError(t('err_province'));
  if (!form.city.trim()) return setError(t('err_city'));

  setSubmitting(true);

  try {
    if (isEditing) {
      // Delete old job first
      await deleteJob(jobToEdit.d_tag, jobToEdit.pubkey);
      markDeleted(jobToEdit.d_tag);
    }

    const dTag = generateDTag();
    const event = {
      kind: 30078,
      pubkey: '',
      created_at: Math.floor(Date.now() / 1000),
      tags: [
        ['d', dTag],
        ['t', 'agentboss'],
        ['t', 'job'],
      ],
      content: JSON.stringify({
        title: form.title.trim(),
        company: form.company.trim(),
        salary_range: form.salary.trim(),
        description: form.description.trim(),
        contact: form.contact.trim(),
      }),
    };

    const signed = await signEvent(event);
    const relay = createRelayClient();
    await relay.connect();
    await relay.publish(signed);
    relay.close();

    if (onSuccess) onSuccess();
    if (onClose) onClose();
  } catch (err) {
    if (err.name === 'NoSignerError') {
      setError(t('err_nip07'));
    } else {
      setError(t('err_post'));
    }
  } finally {
    setSubmitting(false);
  }
};
```

- [ ] **Step 4: 添加 import**

```jsx
import { deleteJob, signEvent } from '../lib/nostr.js';
import { createRelayClient, generateDTag } from '../lib/relay.js';
import { markDeleted } from '../hooks/useDeletedJobs.js';
```

- [ ] **Step 5: 提交**

```bash
git add web/src/components/PublishForm.jsx
git commit -m "$(cat <<'EOF'
feat(web): PublishForm — add jobToEdit prop for edit mode

Pre-fills form, renames title to 'Edit Job', deletes old job
before publishing new one.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: JobCard 编辑按钮

**Files:**
- Modify: `web/src/components/JobCard.jsx`

- [ ] **Step 1: 添加 onEdit prop 和编辑按钮**

```jsx
export function JobCard({ job, onClick, onDelete, onEdit }) {
  // ...
  <div class="job-card-actions">
    <button ...favorite... />
    {onDelete && (
      <button class="job-edit" onClick={(e) => { e.stopPropagation(); onEdit(job); }}>
        {t('edit')}
      </button>
    )}
    {onDelete && (
      <button class="job-delete" ...delete... />
    )}
  </div>
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/JobCard.jsx
git commit -m "$(cat <<'EOF'
feat(web): JobCard — add onEdit prop + edit button

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: JobList props 扩展

**Files:**
- Modify: `web/src/components/JobList.jsx`

- [ ] **Step 1: 添加 onEdit prop，透传给 JobCard**

```jsx
export function JobList({ jobs, loading, error, onJobClick, onRetry, onPublish, onDelete, onEdit }) {
  // ...
  {jobs.map((job) => (
    <JobCard
      key={job.id}
      job={job}
      onClick={onJobClick}
      onDelete={onDelete}
      onEdit={onEdit}
    />
  ))}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/JobList.jsx
git commit -m "$(cat <<'EOF'
feat(web): JobList — pass onEdit prop to JobCard

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: App.jsx — 视图状态 + My Jobs 过滤 + 编辑流程

**Files:**
- Modify: `web/src/app.jsx`

- [ ] **Step 1: 添加视图状态和 myJobs 过滤**

```jsx
const [view, setView] = useState('all');
const [editingJob, setEditingJob] = useState(null);

const myJobs = pubkey ? jobs.filter((j) => j.pubkey === pubkey) : [];
```

- [ ] **Step 2: Navbar tab — 签名后显示「我的职位」**

在 `<Navbar ... onPublish={handlePublishClick} />` 之后添加：

```jsx
{hasSigner && (
  <div class="navbar-tabs">
    <button
      class={`navbar-tab ${view === 'all' ? 'active' : ''}`}
      onClick={() => setView('all')}
    >
      {t('latest_jobs')}
    </button>
    <button
      class={`navbar-tab ${view === 'mine' ? 'active' : ''}`}
      onClick={() => setView('mine')}
    >
      {t('my_jobs_tab')}
    </button>
  </div>
)}
```

- [ ] **Step 3: 侧边栏 myJobs 统计**

```jsx
<div class="stat-item">
  <div class="stat-value">{myJobs.length}</div>
  <div class="stat-label">{t('my_jobs')}</div>
</div>
```

- [ ] **Step 4: 内容区条件渲染**

```jsx
{view === 'mine' ? (
  <>
    <div class="jobs-section-title">
      <span>{t('my_jobs_tab')}</span>
      <span style="color: var(--text-muted); font-size: 11px">
        {loading ? t('loading_jobs') : `${myJobs.length} ${t('jobs_count')}`}
      </span>
    </div>
    <JobList
      jobs={myJobs}
      loading={loading}
      error={error}
      onJobClick={() => {}}
      onRetry={reload}
      onPublish={handlePublishClick}
      onDelete={(j) => setDeleteTarget(j)}
      onEdit={(j) => setEditingJob(j)}
    />
    {!loading && myJobs.length === 0 && (
      <div class="empty-state">
        <div class="empty-state-icon">📝</div>
        <h3>{t('no_my_jobs')}</h3>
        <button class="btn btn-primary" onClick={handlePublishClick}>
          {t('publish_btn')}
        </button>
      </div>
    )}
  </>
) : (
  <>
    <JobList jobs={jobs} loading={loading} error={error} ... />
  </>
)}
```

- [ ] **Step 5: PublishForm 编辑状态 + DeleteModal 互斥**

```jsx
{editingJob && !deleteTarget && (
  <PublishForm
    jobToEdit={editingJob}
    onClose={() => setEditingJob(null)}
    onSuccess={() => { setEditingJob(null); reload(); }}
  />
)}

{deleteTarget && (
  <DeleteModal ... />
)}
```

- [ ] **Step 6: 提交**

```bash
git add web/src/app.jsx
git commit -m "$(cat <<'EOF'
feat(web): App — My Jobs view + edit flow

- view state: 'all' | 'mine'
- myJobs filtered by pubkey
- Navbar tabs for view switching (shown when signer connected)
- sidebar stats: my jobs count
- editingJob → PublishForm edit mode
- deleteTarget and editingJob rendered mutually exclusively

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 添加 Navbar tab 样式

**Files:**
- Modify: `web/src/styles/index.css`

- [ ] **Step 1: 添加 navbar-tab 样式**

```css
/* Navbar Tabs */
.navbar-tabs {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.navbar-tab {
  background: none;
  border: none;
  padding: 4px 12px;
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.navbar-tab:hover {
  background: var(--bg-secondary);
  color: var(--text);
}
.navbar-tab.active {
  background: var(--bg-secondary);
  color: var(--accent);
  font-weight: 500;
}
```

- [ ] **Step 2: 添加 job-edit 按钮样式**

```css
/* Edit Button */
.job-edit {
  background: none;
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #93c5fd;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}
.job-edit:hover {
  background: rgba(59, 130, 246, 0.12);
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/styles/index.css
git commit -m "$(cat <<'EOF'
feat(web): add navbar-tab + job-edit styles

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): My Jobs view + edit/delete own jobs (#42)" \
  --body "$(cat <<'EOF'
## Summary

My Jobs view + edit functionality for Issue #42.

## Changes

- `i18n.js`: `my_jobs`, `my_jobs_tab`, `no_my_jobs`, `edit`, `edit_job` keys
- `PublishForm.jsx`: `jobToEdit` prop — pre-fills form, renames title, deletes old job before publishing
- `JobCard.jsx`: `onEdit` prop — edit button shown on owned jobs
- `JobList.jsx`: `onEdit` prop — passes to JobCard
- `app.jsx`:
  - `view` state: 'all' | 'mine'
  - `editingJob` state for edit flow
  - myJobs filtered by pubkey
  - Navbar tabs (shown when signer connected)
  - Sidebar stats: my jobs count
  - Edit modal + Delete modal rendered mutually exclusively
- `index.css`: `.navbar-tab`, `.job-edit` styles

## Verification

- [ ] My Jobs tab visible only when NIP-07 signer connected
- [ ] My Jobs shows only current user's posts
- [ ] Empty state with CTA when no jobs posted
- [ ] Edit button opens pre-filled PublishForm
- [ ] Edit submits: old job deleted + new job published
- [ ] Sidebar shows my jobs count
- [ ] `npm test` passes

Closes #42.
EOF
)"
```

---

## 注意事项

- `deleteTarget` 和 `editingJob` 互斥：用户不能在编辑状态同时打开删除确认
- `PublishForm` 编辑成功后调用 `reload()` 刷新列表，确保列表最新
- `editingJob.pubkey` 传给 `deleteJob`（从 job 对象获取，而非当前用户 pubkey）
- Navbar tabs 仅在 `hasSigner` 时显示，未签名用户不看到这个功能
