# AgentBoss Job Deletion — 设计文档

## 背景

Issue #39：当前用户无法删除自己发布的职位（kind:30078），职位永久留在 Nostr relay 上。需要实现 NIP-78 删除机制。

## 技术方案：NIP-78 标准删除

**选型：A) NIP-78 标准删除（推荐）**

理由：符合 Nostr 规范，其他客户端也能识别已删除内容，不只是本地过滤。

### NIP-78 删除事件格式

```json
{
  "kind": 5,
  "tags": [
    ["d", "<original_d_tag>"],
    ["a", "30078:<pubkey>:<original_d_tag>"]
  ],
  "content": "职位已删除"
}
```

### 数据流

1. 用户在 JobCard 上点击删除（仅对自己的帖子显示）→ 确认弹窗
2. 构建 kind:5 事件，引用原始 d tag
3. NIP-07 签名 → 发布到 relay
4. relay 收到删除事件后，UI 重新加载职位列表时，该职位不再出现

### 过滤策略

`useJobs` 在处理职位列表时，需要同时查询 kind:5 删除事件（过滤条件：`#a` 引用原始 job event），或者简单起见：**前端存储本地删除列表**（localStorage）来过滤，MVP 阶段足够。

MVP 采用**本地过滤**（localStorage 记录已删除 d_tag），V2 再考虑 relay 端同步删除事件查询。

## 目录结构

```
web/src/
├── lib/
│   └── nostr.js              # + deleteJob(dTag, pubkey) 函数
├── hooks/
│   └── useJobs.js            # + deleteJob(dTag) 到返回值
│   └── useDeletedJobs.js     # 新建：localStorage 管理已删除 d_tag
├── components/
│   └── JobCard.jsx           # + 条件显示删除按钮
│   └── DeleteModal.jsx       # 新建：确认弹窗
```

## NIP-07 deleteJob 实现

```javascript
// web/src/lib/nostr.js
export async function deleteJob(dTag, pubkey) {
  const event = {
    kind: 5,
    tags: [
      ['d', dTag],
      ['a', `30078:${pubkey}:${dTag}`],
    ],
    content: '职位已删除',
    created_at: Math.floor(Date.now() / 1000),
  };
  const signed = await signEvent(event);
  const relay = createRelayClient();
  await relay.connect();
  await relay.publish(signed);
  relay.close();
  return signed;
}
```

## UI 变更

### JobCard 变更

```jsx
// 自己的帖子显示删除按钮
{currentUserPubkey && job.pubkey === currentUserPubkey && (
  <button class="job-delete" onClick={(e) => { e.stopPropagation(); onDelete(job); }}>
    🗑 删除
  </button>
)}
```

### DeleteModal 组件

- 标题："确认删除职位？"
- 内容："删除后将无法恢复。"
- 按钮：取消 / 确认删除
- 确认后调用 `deleteJob(dTag, pubkey)` + `markDeleted(dTag)` + 刷新列表

## 本地删除列表

```javascript
// web/src/hooks/useDeletedJobs.js
const DELETED_KEY = 'agentboss_deleted_jobs';

export function useDeletedJobs() {
  const get = () => JSON.parse(localStorage.getItem(DELETED_KEY) || '[]');
  const add = (dTag) => {
    const list = get();
    if (!list.includes(dTag)) localStorage.setItem(DELETED_KEY, JSON.stringify([...list, dTag]));
  };
  const isDeleted = (dTag) => get().includes(dTag);
  return { isDeleted, markDeleted: add };
}
```

## 测试

| 测试 | 内容 |
|------|------|
| `deleteJob` 函数 | 构造 kind:5 事件，签名成功 |
| `useDeletedJobs` | add → isDeleted 返回 true |
| JobCard | 自己的帖子有删除按钮，别人的没有 |
| DeleteModal | 点击确认后调用 deleteJob |

## 相关文件

- `web/src/lib/nostr.js` — 添加 `deleteJob()`
- `web/src/hooks/useDeletedJobs.js` — 新建
- `web/src/hooks/useJobs.js` — 返回值加 `deleteJob`，过滤已删除职位
- `web/src/components/JobCard.jsx` — 条件显示删除按钮
- `web/src/components/DeleteModal.jsx` — 新建
- `docs/superpowers/specs/2026-03-26-agentboss-job-deletion-design.md` — 本文档
