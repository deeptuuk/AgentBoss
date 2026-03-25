# AgentBoss 前端测试覆盖 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved

---

## 1. 背景

Issue #25：`web/` 目录无测试框架，前端代码无自动化测试保障。Jarvis 强调"记得测试啊"。

当前前端组件：JobCard、JobList、PublishForm、Navbar。Hooks：useJobs、useFavorites。

## 2. 目标

- 添加 vitest 测试框架
- 为 JobCard、JobList、useJobs、useFavorites 编写单元测试
- `npm test` 通过，无 regression 风险

## 3. 技术选型

| 工具 | 用途 |
|------|------|
| `vitest` ^1.3.0 | 测试运行器，Vite 原生集成 |
| `@testing-library/preact` ^3.2.3 | 组件 DOM 查询测试 |
| `jsdom` ^24.0.0 | 浏览器环境（localStorage 模拟）|

**不采用 MSW WebSocket：** relay 集成测试作为 future issue，MVP 阶段复杂度不划算。

## 4. 文件结构

```
web/
  vitest.config.js
  package.json          ← 添加测试依赖
  src/
    __tests__/
      JobCard.test.jsx
      JobList.test.jsx
      useJobs.test.js
      useFavorites.test.js
```

## 5. Mock 策略

### 5.1 Relay Client Mock

```javascript
// 每个测试中内联 mock，无需全局 setup
vi.mock('../lib/relay.js', () => ({
  createRelayClient: () => ({
    connect: vi.fn().mockResolvedValue(undefined),
    subscribe: vi.fn(),
    close: vi.fn(),
    onEvent: vi.fn(),
    onEOSE: vi.fn((cb) => cb()),  // 同步触发，模拟 relay 响应
  }),
}));
```

### 5.2 localStorage Mock（jsdom 环境）

```javascript
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });
```

每个测试前重置：
```javascript
beforeEach(() => {
  localStorageMock.getItem.mockReturnValue('[]');
  localStorageMock.setItem.mockClear();
});
```

## 6. 测试用例

### 6.1 JobCard.test.jsx

| 用例 | 描述 |
|------|------|
| 渲染标题/公司 | `getByText(job.title)`，`getByText(job.company)` |
| 渲染省份/薪资标签 | 有 province/salary 时显示对应 tag |
| 无省份/薪资时标签隐藏 | 条件渲染验证 |
| 收藏按钮：未收藏显示 ☆ | 初始状态 class 不含 `active` |
| 收藏按钮：已收藏显示 ★ | mock localStorage 预填数据 |
| 收藏按钮：点击切换 | `userEvent.click`，验证 toggle 调用 |
| 时间显示 | 渲染 `timeAgo` 输出 |

### 6.2 JobList.test.jsx

| 用例 | 描述 |
|------|------|
| loading 状态：显示骨架屏 | `getAllByClass('skeleton')`，数量 4 |
| error 状态：显示错误信息 | `getByText(error)` |
| 空状态：无职位时显示 | `getByText('暂无职位')` |
| 正常列表：渲染 JobCard | `getAllByRole('article')` 数量等于 jobs.length |

### 6.3 useJobs.test.js

| 用例 | 描述 |
|------|------|
| 返回 `{ jobs, loading, error, reload }` | 结构验证 |
| loading 初始 true | 第一个状态 |
| onEOSE 触发后 loading=false | 完整流程 |
| onEOSE 触发后 jobs 有数据 | 模拟 relay 返回 |
| searchQuery 过滤 | 过滤后 jobs.length < allJobs.length |
| error 时 error 不为 null | WebSocket 异常路径 |
| reload 函数重新触发加载 | `loadJobs` 被调用两次 |

### 6.4 useFavorites.test.js

| 用例 | 描述 |
|------|------|
| 初始 count=0 | localStorage 为空 |
| toggle 添加收藏 | count 从 0 → 1 |
| toggle 移除收藏 | count 从 1 → 0 |
| isFavorite 正确返回 true/false | 独立于 toggle |
| 多个 job 独立管理 | 切换不同 job id |

## 7. 实施步骤

1. `package.json` 添加 vitest + @testing-library/preact + jsdom
2. 创建 `vitest.config.js`
3. 创建 `web/src/__tests__/` 目录
4. 编写 JobCard.test.jsx
5. 编写 JobList.test.jsx
6. 编写 useJobs.test.js
7. 编写 useFavorites.test.js
8. `npm test` 验证全部通过
9. GitHub Actions 添加 test CI（可选）

## 8. 验证标准

- [ ] `npm test` 全部通过
- [ ] JobCard：5 个用例通过
- [ ] JobList：4 个用例通过
- [ ] useJobs：5 个用例通过
- [ ] useFavorites：4 个用例通过
- [ ] 总计：18 个测试用例

## 9. 不在本次范围

- PublishForm 测试（表单交互复杂，future issue）
- Navbar 测试（DOM 交互少，future issue）
- Relay 集成测试（需真实 relay 或完整 mock server）
- E2E 测试（Playwright/Cypress）
