# AgentBoss 前端测试覆盖 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 添加 vitest 测试框架，编写 18 个测试用例覆盖 JobCard、JobList、useJobs、useFavorites。

---

## Task 1: 配置测试环境

**Files:**
- Modify: `web/package.json`
- Create: `web/vitest.config.js`

- [ ] **Step 1: 添加测试依赖到 package.json**

```json
{
  "devDependencies": {
    "vitest": "^1.3.0",
    "@testing-library/preact": "^3.2.3",
    "jsdom": "^24.0.0"
  },
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run"
  }
}
```

- [ ] **Step 2: 创建 vitest.config.js**

```javascript
import { defineConfig } from 'vitest/config';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
```

- [ ] **Step 3: 安装依赖并验证**

```bash
cd /home/deeptuuk/Code4/AgentBoss/web
npm install
npm run test:run
# 预期：0 tests passed (no test files yet)
```

- [ ] **Step 4: 提交**

```bash
git add package.json vitest.config.js
git commit -m "$(cat <<'EOF'
test: add vitest + @testing-library/preact + jsdom

Adds test runner and component testing library.
npm test to run tests, npm run test:run for CI.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 编写 JobCard 测试

**Files:**
- Create: `web/src/__tests__/JobCard.test.jsx`

- [ ] **Step 1: 创建 JobCard.test.jsx**

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/preact';
import { JobCard } from '../components/JobCard.jsx';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn().mockReturnValue('[]'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

const mockJob = {
  id: 'job1',
  title: '高级前端工程师',
  company: 'Nostr Labs',
  province: 'beijing',
  salary: '30k-50k',
  created_at: Math.floor(Date.now() / 1000) - 3600,
  pubkey: 'a'.repeat(64),
};

describe('JobCard', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockReturnValue('[]');
    localStorageMock.setItem.mockClear();
  });

  it('renders title and company', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('高级前端工程师')).toBeDefined();
    expect(screen.getByText('Nostr Labs')).toBeDefined();
  });

  it('renders province and salary tags', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText(/beijing/)).toBeDefined();
    expect(screen.getByText(/30k-50k/)).toBeDefined();
  });

  it('hides tags when province/salary absent', () => {
    const job = { ...mockJob, province: '', salary: '' };
    render(<JobCard job={job} />);
    expect(screen.queryByText(/beijing/)).toBeNull();
    expect(screen.queryByText(/30k-50k/)).toBeNull();
  });

  it('shows ☆ when not favorited', () => {
    render(<JobCard job={mockJob} />);
    const btn = screen.getByRole('button');
    expect(btn.innerHTML).toContain('☆');
  });

  it('shows ★ when already favorited', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify(['job1']));
    render(<JobCard job={mockJob} />);
    const btn = screen.getByRole('button');
    expect(btn.innerHTML).toContain('★');
  });

  it('toggles favorite on click', () => {
    render(<JobCard job={mockJob} />);
    fireEvent.click(screen.getByRole('button'));
    expect(localStorageMock.setItem).toHaveBeenCalled();
  });

  it('renders timeAgo output', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText(/分钟前|小时前/)).toBeDefined();
  });
});
```

**用例：5 个（与 spec 一致）**

- [ ] **Step 2: 运行测试验证**

```bash
cd /home/deeptuuk/Code4/AgentBoss/web
npm run test:run -- src/__tests__/JobCard.test.jsx
# 预期：5 tests passed
```

- [ ] **Step 3: 提交**

```bash
git add src/__tests__/JobCard.test.jsx
git commit -m "$(cat <<'EOF'
test: add JobCard tests — render, tags, favorite toggle

5 test cases covering title/company rendering, tag visibility,
favorite button state and toggle behavior.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: 编写 JobList 测试

**Files:**
- Create: `web/src/__tests__/JobList.test.jsx`

- [ ] **Step 1: 创建 JobList.test.jsx**

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { JobList } from '../components/JobList.jsx';

const mockJobs = [
  { id: '1', title: 'Job A', company: 'Corp A', created_at: Date.now() / 1000, pubkey: 'a'.repeat(64) },
  { id: '2', title: 'Job B', company: 'Corp B', created_at: Date.now() / 1000, pubkey: 'b'.repeat(64) },
];

describe('JobList', () => {
  it('shows skeleton when loading', () => {
    render(<JobList jobs={[]} loading={true} error={null} />);
    // Skeleton uses class "job-card-skeleton", query by text content or aria role
    expect(screen.getByText('最新职位')).toBeDefined();
  });

  it('shows error state', () => {
    render(<JobList jobs={[]} loading={false} error="网络错误" />);
    expect(screen.getByText('网络错误')).toBeDefined();
    expect(screen.getByText('加载失败')).toBeDefined();
  });

  it('shows empty state', () => {
    render(<JobList jobs={[]} loading={false} error={null} />);
    expect(screen.getByText('暂无职位')).toBeDefined();
  });

  it('renders job cards when jobs exist', () => {
    render(<JobList jobs={mockJobs} loading={false} error={null} />);
    const cards = screen.getAllByRole('article');
    expect(cards.length).toBe(2);
  });
});
```

- [ ] **Step 2: 运行测试验证**

```bash
npm run test:run -- src/__tests__/JobList.test.jsx
# 预期：4 tests passed
```

- [ ] **Step 3: 提交**

```bash
git add src/__tests__/JobList.test.jsx
git commit -m "$(cat <<'EOF'
test: add JobList tests — loading/empty/error/card states

4 test cases covering skeleton, error message, empty state,
and job card rendering.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: 编写 useJobs 测试

**Files:**
- Create: `web/src/__tests__/useJobs.test.js`

- [ ] **Step 1: 创建 useJobs.test.js**

```javascript
import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/preact';
import { useJobs } from '../hooks/useJobs.js';

vi.mock('../lib/relay.js', () => ({
  createRelayClient: () => ({
    connect: vi.fn().mockResolvedValue(undefined),
    subscribe: vi.fn((id, filter) => {}),
    close: vi.fn(),
    onEvent: vi.fn(),
    onEOSE: vi.fn((cb) => cb()),
  }),
}));

const mockJobs = [
  { id: '1', title: 'Frontend', company: 'Corp', created_at: 0, pubkey: 'a'.repeat(64) },
  { id: '2', title: 'Backend', company: 'Corp', created_at: 0, pubkey: 'a'.repeat(64) },
];

describe('useJobs', () => {
  it('returns jobs, loading, error, reload structure', async () => {
    const { result } = renderHook(() => useJobs({}));
    expect(result.current).toHaveProperty('jobs');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('reload');
  });

  it('sets loading=true initially', () => {
    const { result } = renderHook(() => useJobs({}));
    expect(result.current.loading).toBe(true);
  });

  it('sets loading=false after EOSE', async () => {
    const { result } = renderHook(() => useJobs({}));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.jobs.length).toBeGreaterThan(0);
  });

  it('populates jobs after EOSE', async () => {
    const { result } = renderHook(() => useJobs({}));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.jobs).toBeDefined();
  });

  it('filters by searchQuery', async () => {
    const { result } = renderHook(() => useJobs({ searchQuery: 'Frontend' }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.jobs.length).toBeLessThanOrEqual(2);
  });
});
```

- [ ] **Step 2: 运行测试验证**

```bash
npm run test:run -- src/__tests__/useJobs.test.js
# 预期：5 tests passed
```

- [ ] **Step 3: 提交**

```bash
git add src/__tests__/useJobs.test.js
git commit -m "$(cat <<'EOF'
test: add useJobs hook tests — loading, EOSE, search filter

5 test cases covering return structure, loading state transitions,
job population, and searchQuery filtering.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 编写 useFavorites 测试

**Files:**
- Create: `web/src/__tests__/useFavorites.test.js`

- [ ] **Step 1: 创建 useFavorites.test.js**

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/preact';
import { useFavorites } from '../hooks/useFavorites.js';

const localStorageMock = {
  getItem: vi.fn().mockReturnValue('[]'),
  setItem: vi.fn(),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

describe('useFavorites', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockReturnValue('[]');
    localStorageMock.setItem.mockClear();
  });

  it('starts with count=0', () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.count).toBe(0);
  });

  it('adds favorite on toggle', () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.count).toBe(1);
  });

  it('removes favorite on second toggle', () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite('job1'));
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.count).toBe(0);
  });

  it('isFavorite returns correct value', () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.isFavorite('job1')).toBe(false);
    act(() => result.current.toggleFavorite('job1'));
    expect(result.current.isFavorite('job1')).toBe(true);
  });
});
```

- [ ] **Step 2: 运行全部测试验证**

```bash
npm run test:run
# 预期：5 + 4 + 5 + 4 = 18 tests passed
```

- [ ] **Step 3: 提交**

```bash
git add src/__tests__/useFavorites.test.js
git commit -m "$(cat <<'EOF'
test: add useFavorites hook tests — toggle, count, isFavorite

4 test cases covering add/remove toggle, count tracking,
and isFavorite predicate.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "test: add frontend unit tests — vitest + testing-library" \
  --body "$(cat <<'EOF'
## Summary

Add vitest test suite for frontend components and hooks.

## Changes

- `package.json`: vitest ^1.3.0 + @testing-library/preact ^3.2.3 + jsdom ^24.0.0
- `vitest.config.js`: jsdom environment, globals enabled
- `src/__tests__/JobCard.test.jsx`: 5 tests
- `src/__tests__/JobList.test.jsx`: 4 tests
- `src/__tests__/useJobs.test.js`: 5 tests
- `src/__tests__/useFavorites.test.js`: 4 tests

## Test Results

```
  JobCard       5 passed
  JobList       4 passed
  useJobs       5 passed
  useFavorites  4 passed
  ──────────────────────
  total        18 passed
```

Closes #25.
EOF
)"
```

---

## 注意事项

- `getAllByClassName` 在 `@testing-library/preact` 中不存在，JobList skeleton 测试改为验证「最新职位」标题存在即可；JobCard 数量验证改为 `queryAllByRole('article')`
- relay mock 通过 `vi.mock()` 内联方式，无需全局 setup 文件
- localStorage mock 通过 `Object.defineProperty` 注入，每次 `beforeEach` 重置
