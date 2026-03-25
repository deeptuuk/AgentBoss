# AgentBoss 健壮性改进 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved
**Issue:** #31

---

## 1. 背景

代码审查发现两个生产级问题：

1. **`hexToNpub()` 是 stub**：返回 hex 而非 bech32 npub 格式
2. **Relay 无降级**：单 relay 无 fallback，可用性差

## 2. 目标

- 实现纯 JS bech32 npub 格式转换，Navbar 显示标准 npub 格式
- Relay 连接失败时自动降级到备用 relay

---

## 3. 技术方案

### 3.1 hexToNpub / npubToHex

**无第三方依赖**，纯 JS 实现 bech32 编码。

bech32 结构：
- Human-readable part (HRP): `npub`
- Data part: 32-byte hex pubkey → 5-bit base32 编码

```javascript
// web/src/lib/nostr.js

// Character tables for bech32
const BECH32_CHARS = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';
const BECH32M_CONST = 0x2bc830a3;

function bech32Polymod(values) { /* ... */ }
function bech32HrpExpand(hrp) { /* ... */ }
function bech32VerifyChecksum(hrp, data) { /* ... */ }
function bech32CreateChecksum(hrp, data) { /* ... */ }
function bech32Encode(hrp, data) { /* ... */ }
function bech32Decode(str) { /* ... */ }

function hexToBase5(hex) { /* hex string → base5 array */ }
function base5ToHex(b5) { /* base5 array → hex string */ }

export function hexToNpub(hex) {
  const data = hexToBase5(hex.padStart(64, '0'));
  return bech32Encode('npub', data);
}

export function npubToHex(npub) {
  const { data } = bech32Decode(npub);
  return base5ToHex(data);
}
```

**Navbar Badge 更新**：`pubkey.slice(0,8)` → `hexToNpub(pubkey).slice(0, 12) + '…'`

### 3.2 Relay 降级

```javascript
// web/src/lib/relay.js

const RELAYS = [
  'wss://relay.nostr.band',
  'wss://nos.lol',
  'wss://relay.damus.io',
];

export function createRelayClient() {
  let ws = null;
  let currentRelayIndex = 0;
  let onEvent = null;
  let onEOSE = null;

  async function connect() {
    return new Promise((resolve, reject) => {
      const relayUrl = RELAYS[currentRelayIndex];
      ws = new WebSocket(relayUrl);

      ws.onopen = () => resolve();
      ws.onerror = (e) => {
        // Try next relay
        if (currentRelayIndex < RELAYS.length - 1) {
          currentRelayIndex++;
          ws.close();
          connect().then(resolve).catch(reject);
        } else {
          reject(new Error(`All relays failed`));
        }
      };
      // ... rest unchanged
    });
  }
}
```

---

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/lib/nostr.js` | 新增 bech32 编解码函数 + hexToNpub + npubToHex |
| `web/src/lib/relay.js` | relay 降级逻辑：失败时自动切换 |
| `web/src/components/Navbar.jsx` | Badge 显示 npub1... 格式 |
| `web/src/__tests__/nostr.test.js` | 新增 bech32 + npub 转换测试 |

---

## 5. 测试用例

### hexToNpub / npubToHex
- `hexToNpub` → 以 `npub1` 开头
- `npubToHex(npubToHex(hex)) === hex` 往返一致
- 无效 npub 格式抛出错误

### Relay 降级
- 第一 relay 失败时自动连接第二 relay
- 所有 relay 失败时 reject 并报错
- 正常连接时行为不变

---

## 6. 不在本次范围

- Relay 连接池（并发多 relay 取并集）
- NIP-19 TLV 解析（完整 note/bech32）
- relay.damus.io 降级到更多 relay
