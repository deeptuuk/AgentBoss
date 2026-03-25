# RegionMapping 类型一致化修复 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `RegionMapping.province_name_to_code` / `city_name_to_code` 返回 string 而非 int 的类型不一致，使类型注解与实际返回值一致。

**Architecture:** 仅修改 2 个方法的签名和返回值 + 更新对应测试，无生产调用方变更。

**Tech Stack:** Python 3.11+, pytest

---

## 文件变更概览

| 文件 | 变更类型 |
|------|---------|
| `cli/models.py` | 修改：2 个方法的签名和返回值 |
| `tests/test_models.py` | 修改：测试断言预期值 |

---

## Task 1: 修复 `province_name_to_code` 和 `city_name_to_code` 的类型

**Files:**
- Modify: `cli/models.py:61-71`
- Test: `tests/test_models.py`（先读现有测试确认断言内容）

- [ ] **Step 1: 阅读现有测试确认断言内容**

```bash
cd /home/deeptuuk/Code3/AgentBoss
grep -n "province_name_to_code\|city_name_to_code\|test_name_to_code" tests/test_models.py
```

确认现有断言中的预期返回值（如 `"1"` / `"101"` 形式）。

- [ ] **Step 2: 修改 `cli/models.py`**

将 `cli/models.py` 中两个方法修改为：

```python
def province_name_to_code(self, name: str) -> int | None:
    for code, n in self.provinces.items():
        if n == name:
            return int(code)
    return None

def city_name_to_code(self, name: str) -> int | None:
    for code, n in self.cities.items():
        if n == name:
            return int(code)
    return None
```

- [ ] **Step 3: 修改 `tests/test_models.py`**

将断言中的预期返回值从 string 改为 int：

```python
# province_name_to_code 测试
assert mapping.province_name_to_code("北京") == 1       # 原来是 "1"
assert mapping.province_name_to_code("不存在") is None

# city_name_to_code 测试
assert mapping.city_name_to_code("北京市") == 101       # 原来是 "101"
assert mapping.city_name_to_code("不存在") is None
```

- [ ] **Step 4: 运行全部测试验证通过**

```bash
source /home/deeptuuk/Code3/code_env/bin/activate
python -m pytest tests/test_models.py -v
```
预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add cli/models.py tests/test_models.py
git commit -m "$(cat <<'EOF'
fix(models): return int instead of str in RegionMapping name_to_code methods

Type annotation declared int | None but methods returned str | None.
No production callers; RegionResolver uses storage.get_region() directly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: 推送**

```bash
git push
```

- [ ] **Step 7: 提 PR 给 nicholasyangyang**

```bash
# 从 deeptuuk fork 创建 PR
gh pr create --repo nicholasyangyang/AgentBoss --title "fix: return int in RegionMapping name_to_code methods" --body "Fix type inconsistency in province_name_to_code / city_name_to_code. Closes #15."
```

---

## 相关文件

- Spec: `docs/superpowers/specs/2026-03-25-agentboss-regionmapping-type-fix-design.md`
- Issue: https://github.com/nicholasyangyang/AgentBoss/issues/15
