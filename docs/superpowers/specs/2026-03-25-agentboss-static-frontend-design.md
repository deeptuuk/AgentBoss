# AgentBoss 静态前端 — 设计文档

## 背景

Issue #18：将 AgentBoss 的 `web/` 目录从 FastAPI Python 应用改造为纯静态前端，前端直接与 Nostr relay 通信，使普通用户在浏览器中即可使用，无需安装 CLI 工具。

## 技术选型

| 项目 | 选择 | 理由 |
|------|------|------|
| 前端框架 | **Preact + Vite** | ~3KB 体积，React API 兼容，热更新+构建优化，比纯 HTML 好维护 |
| Nostr 通信 | **Relay 网关** | WebSocket 直接连 relay 有 CORS 问题，网关（nip05.info 等）已解决跨域 |
| 身份认证 | **NIP-07 浏览器扩展** | Alby、nos2x 等广泛使用，Nostr 生态标准 |
| 收藏存储 | **localStorage** | MVP 阶段足够，IndexedDB V2 再考虑 |
| Relay 列表 | **公开 relay 列表（可配置）** | MVP 硬编码可靠 relay，未来用户可配置 |

## MVP 功能范围

| 功能 | 状态 | 说明 |
|------|------|------|
| 浏览职位 | ✅ MVP | 静态 + relay 直连 |
| 搜索职位 | ✅ MVP | 同上 |
| 发布职位 | ✅ MVP | NIP-07 签名 |
| 收藏职位 | ✅ MVP | localStorage |
| 申请职位 | ✅ MVP | 公开 Application event（kind 31970） |
| 私信雇主 | ❌ V2 | 浏览器无法 NIP-04 加密 |
| 用户注册/登录 | ✅ MVP | NIP-07 替代，pubkey 即身份 |

## 架构

```
┌─────────────────────────────────────────────────────────┐
│  Browser (NIP-07 Extension)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Preact App  │  │ Nostr SDK    │  │ localStor. │ │
│  │  (Vite)     │──│ (via relay   │  │ (favs)    │ │
│  └──────────────┘  │  gateway)    │  └────────────┘ │
└──────────────────────│──────────────│─────────────────┘
                       │              │
                       ▼              ▼
              ┌─────────────────────┐
              │   Relay Gateway     │
              │ (nip05.info 等)     │
              └──────────┬──────────┘
                         │ WebSocket
                         ▼
              ┌─────────────────────┐
              │   Nostr Relays      │
              │ (nos.lol, damus.io) │
              └─────────────────────┘
```

## 目录结构

```
web/
├── index.html              # Vite 入口
├── vite.config.js         # Vite 配置
├── package.json            # Preact + Vite 依赖
├── src/
│   ├── main.jsx           # Preact 入口
│   ├── app.jsx            # 根组件
│   ├── components/        # UI 组件
│   │   ├── JobCard.jsx    # 职位卡片
│   │   ├── JobList.jsx     # 职位列表
│   │   ├── JobDetail.jsx   # 职位详情
│   │   ├── PublishForm.jsx # 发布表单
│   │   ├── SearchBar.jsx   # 搜索栏
│   │   └── Navbar.jsx      # 导航栏
│   ├── hooks/             # Preact hooks
│   │   ├── useJobs.js      # 职位数据 hook
│   │   ├── useRelay.js     # Relay 连接 hook
│   │   └── useFavorites.js  # 收藏 hook
│   ├── lib/
│   │   ├── nostr.js        # Nostr SDK 封装
│   │   └── relay.js        # Relay 网关客户端
│   └── styles/
│       └── index.css      # 全局样式
└── dist/                  # Vite 构建输出（部署用）
```

## 数据流

### 浏览/搜索职位
1. 用户打开页面 → Preact App 加载
2. `useJobs` hook 调用 relay 网关，查询 kind:30078 + tag:agentboss/job 事件
3. 解析 event content（JSON）→ 渲染职位列表
4. 搜索：过滤本地数据或发新查询

### 发布职位
1. 用户填写表单 → 点击发布
2. 调用 `window.nostr.signEvent(event)`（NIP-07）
3. 用户在扩展中确认签名
4. 发布签名事件到 relay

### 收藏职位
1. 用户点击收藏按钮 → `useFavorites` hook 读写 localStorage
2. 无网络请求，纯本地

### 申请职位
1. 用户点击申请 → 构建 kind:31970 Application event
2. NIP-07 签名 → 发布到 relay

## NIP-07 集成

```javascript
// 检测 NIP-07 扩展
const getSigner = () => {
  if (window.nostr) {
    return window.nostr;
  }
  // 兜底：提示安装扩展
  throw new Error('请安装 NIP-07 扩展（如 Alby）');
};

// 签名发布职位
const publishJob = async (jobContent) => {
  const event = {
    kind: 30078,
    tags: [['d', generateDTag()], ['t', 'agentboss'], ['t', 'job']],
    content: JSON.stringify(jobContent),
    created_at: Math.floor(Date.now() / 1000),
  };
  const signed = await window.nostr.signEvent(event);
  await relay.publish(signed);
};
```

## Relay 网关配置

```javascript
const RELAY_GATEWAYS = [
  'wss://relay.nostr.band',
  'wss://nos.lol',
];

// 优先使用支持 CORS 的网关
const gateway = RELAY_GATEWAYS[0];
```

## GitHub Pages 部署

Vite 构建输出到 `web/dist/`，部署方式：

**方案 A（推荐）：子目录部署**
- `vite.config.js` 设置 `base: '/AgentBoss/'`
- 构建后 `dist/` 内容复制到 `docs/` 目录
- GitHub Pages 从 `master/docs` 托管

**方案 B：新分支**
- `git checkout -b gh-pages`
- 构建后 `dist/` 内容推送到 `gh-pages` 分支
- GitHub Pages 从 `gh-pages` 分支托管

## 设计原则

- **Preact first**：只用 Preact，不引入 React 完整生态
- **零后端**：纯静态，所有数据通过 Nostr relay
- **渐进增强**：无 NIP-07 扩展时提示安装，不做降级
- **移动优先**：响应式设计，支持手机浏览

## 相关文件

- `web/` — 新前端目录（替代现有 FastAPI web/）
- `docs/` — GitHub Pages 文档站点（保留）
