# AgentBoss

基于 Nostr 的去中心化招聘平台。

## 功能

### 核心功能
- 发布职位 (NIP-04 加密 DM + kind:31970 事件)
- 搜索/过滤职位
- 申请职位 (kind:31970 申请事件)
- 雇主回复申请

### Relay Federation
职位发布可以跨越多个 Nostr relay，扩展职位覆盖范围。

#### Federation 命令
```bash
# 创建 Federation
agentboss federation create <名称> <relay1> [relay2...]

# 加入 Federation
agentboss federation join federation:<npub_hex>:<名称>

# 列出已加入的 Federation
agentboss federation list

# 退出 Federation
agentboss federation leave <federation_id>
```

#### 多 Relay 操作
```bash
# 从 Federation 获取职位
agentboss fetch --federation <名称>

# 发布职位到 Federation
agentboss publish --federation <名称> --province <省> --city <城市> --title <标题> --company <公司>
```

## 安装
```bash
# 使用 uv 创建虚拟环境
uv venv .env --python 3.12
source .env/bin/activate  # Linux/Mac
# .env\Scripts\activate   # Windows

# 安装 pip 和项目
uv pip install pip

# 方式一：pip 安装
pip install -e .

# 方式二：uv lock 管理依赖
uv lock
uv sync
```

## 运行环境
使用 `uv` 管理虚拟环境确保一致性：
```bash
# 激活环境（每次操作前）
source .env/bin/activate

# 运行测试
pytest tests/ -v

# 运行 CLI
agentboss <命令>
```

## 快速开始
```bash
# 1. 登录
agentboss login --key <nsec>

# 2. 创建 Federation
agentboss federation create techjobs wss://relay1.example.com wss://relay2.example.com

# 3. 发布职位
agentboss publish --province 北京 --city 北京市 --title "高级工程师" --company "科技公司"

# 4. 获取职位
agentboss fetch
agentboss list
```

## 职位事件 (kind:31970)
```json
{
  "content": "{\"title\":\"...\",\"company\":\"...\",\"salary_range\":\"...\",\"description\":\"...\"}",
  "tags": [
    ["d", "<unique-id>"],
    ["t", "agentboss"],
    ["t", "job"],
    ["province", "<code>"],
    ["city", "<code>"]
  ]
}
```

## Federation 邀请码格式
```
federation:<npub_hex>:<名称>
```

Federation 事件 (kind:31990)：
```json
{
  "content": "[\"wss://relay1.example.com\", \"wss://relay2.example.com\"]",
  "tags": [["d", "<federation_name>"], ["t", "agentboss"], ["t", "federation"]]
}
```
