# AgentBoss RegionMapping 类型一致化修复 — 设计文档

## 背景

`RegionMapping.province_name_to_code()` 和 `RegionMapping.city_name_to_code()` 方法声明返回 `int | None`，但实际返回 JSON dict 的 string key，导致类型不一致。

这两个方法在生产代码（`cli/` 目录）中**无调用方**，是死代码。`RegionResolver` 实际使用 `storage.get_region()` + `int(r["code"])` 直接返回 int。但死代码中的类型不一致会阻碍未来使用，并造成类型系统脏污。

## 问题代码

**文件：** `cli/models.py:61-71`

```python
def province_name_to_code(self, name: str) -> str | None:  # ❌ 声明与类型标注矛盾
    for code, n in self.provinces.items():
        if n == name:
            return code  # 返回 str，注解说 int
    return None

def city_name_to_code(self, name: str) -> str | None:  # ❌ 同上
    for code, n in self.cities.items():
        if n == name:
            return code
    return None
```

## 修复方案

### 修正方法签名和返回值

```python
def province_name_to_code(self, name: str) -> int | None:
    for code, n in self.provinces.items():
        if n == name:
            return int(code)  # 转为 int
    return None

def city_name_to_code(self, name: str) -> int | None:
    for code, n in self.cities.items():
        if n == name:
            return int(code)
    return None
```

### 注意事项

- `provinces: dict[str, str]` 和 `cities: dict[str, str]` **保持不变**（JSON key 必须是 string）
- `RegionResolver` 层**无需改动**（已正确返回 int）
- 前导零问题不涉及：JSON 层 string 保持不变，不丢数据

## 测试修正

**文件：** `tests/test_models.py`

现有测试断言需将预期返回值从 string 改为 int（测试 fixture 使用简化值 `1` / `101`）：

```python
# province_name_to_code 测试
assert mapping.province_name_to_code("北京") == 1       # 原来是 "1"
assert mapping.province_name_to_code("不存在") is None

# city_name_to_code 测试
assert mapping.city_name_to_code("北京市") == 101       # 原来是 "101"
assert mapping.city_name_to_code("不存在") is None
```

## 设计原则

- **最小化修复**：仅修改 2 个方法的签名和返回值
- **向后兼容**：死代码，无生产调用方，风险极低
- **类型干净**：使类型注解与实际返回值一致

## 相关文件

- `cli/models.py` — RegionMapping 类
- `tests/test_models.py` — 单元测试
