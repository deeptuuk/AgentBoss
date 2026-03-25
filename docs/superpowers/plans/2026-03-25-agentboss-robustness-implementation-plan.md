# AgentBoss 健壮性改进 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 hexToNpub/npubToHex bech32 转换 + relay 降级，修复 #31

---

## Task 1: 实现 bech32 编解码

**Files:**
- Modify: `web/src/lib/nostr.js`

- [ ] **Step 1: 添加 bech32 核心函数**

在 `nostr.js` 末尾添加：

```javascript
// ── Bech32 (npub/note) — pure JS, no dependency ─────────

const BECH32_CHARS = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';

function bech32Polymod(values) {
  const GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
  let chk = 1;
  for (const v of values) {
    const b = chk >> 25;
    chk = ((chk & 0x1ffffff) << 5) ^ v;
    for (let i = 0; i < 5; i++) {
      if ((b >> i) & 1) chk ^= GEN[i];
    }
  }
  return chk;
}

function bech32HrpExpand(hrp) {
  return hrp.split('').map((c) => c.charCodeAt(0) >> 5).concat([0])
    .concat(hrp.split('').map((c) => c.charCodeAt(0) & 31));
}

function bech32VerifyChecksum(hrp, data) {
  const poly = bech32Polymod(bech32HrpExpand(hrp).concat(data));
  return poly === 1 || poly === BECH32M_CONST;
}

function bech32CreateChecksum(hrp, data) {
  const values = bech32HrpExpand(hrp).concat(data).concat([0, 0, 0, 0, 0, 0]);
  const poly = bech32Polymod(values);
  return [(poly >> 25) & 31, (poly >> 20) & 31, (poly >> 15) & 31,
           (poly >> 10) & 31, (poly >> 5) & 31, poly & 31];
}

function bech32Encode(hrp, data) {
  const combined = data.concat(bech32CreateChecksum(hrp, data));
  return hrp + '1' + combined.map((v) => BECH32_CHARS[v]).join('');
}

function bech32Decode(str) {
  const idx = str.lastIndexOf('1');
  if (idx < 1 || idx + 7 > str.length) throw new Error('Invalid bech32');
  const hrp = str.slice(0, idx);
  const data = str.slice(idx + 1).toLowerCase().split('')
    .map((c) => { const i = BECH32_CHARS.indexOf(c); return i < 0 ? -1 : i; });
  if (data.some((v) => v < 0)) throw new Error('Invalid bech32 char');
  return { hrp, data: data.slice(0, -6) };
}

function bech32MVerifyChecksum(hrp, data) {
  return bech32Polymod(bech32HrpExpand(hrp).concat(data)) === BECH32M_CONST;
}

// ── Hex ↔ Base5 ────────────────────────────────────────

function hexToBase5(hex) {
  let bits = 0, count = 0, out = [];
  for (const c of hex) {
    bits = (bits << 4) | parseInt(c, 16);
    count += 4;
    while (count >= 5) { out.push((bits >> (count - 5)) & 31); count -= 5; }
  }
  if (count > 0) out.push((bits << (5 - count)) & 31);
  return out;
}

function base5ToHex(b5) {
  let bits = 0, count = 0, out = '';
  for (const v of b5) {
    bits = (bits << 5) | v;
    count += 5;
    while (count >= 4) { out += ((bits >> (count - 4)) & 15).toString(16); count -= 4; }
  }
  return out;
}
```

- [ ] **Step 2: 实现 hexToNpub / npubToHex，替换 stub**

删除原有 `hexToNpub` stub，替换为：

```javascript
export function hexToNpub(hex) {
  const padded = hex.padStart(64, '0');
  return bech32Encode('npub', hexToBase5(padded));
}

export function npubToHex(npub) {
  const { hrp, data } = bech32Decode(npub);
  if (hrp !== 'npub') throw new Error('Invalid npub');
  if (!bech32MVerifyChecksum(hrp, data.concat(bech32CreateChecksum(hrp, data)))) {
    throw new Error('Invalid npub checksum');
  }
  return base5ToHex(data);
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/lib/nostr.js
git commit -m "$(cat <<'EOF'
feat(web): pure-JS bech32 npub encoding — hexToNpub/npubToHex

bech32 bech32M checksum, base5/hex conversion.
No third-party dependency.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: 更新 Navbar 显示 npub 格式

**Files:**
- Modify: `web/src/components/Navbar.jsx`

- [ ] **Step 1: 更新 Navbar 导入和使用**

在 `Navbar.jsx` 中：

```javascript
import { hexToNpub } from '../lib/nostr.js';

// 在 pubkey badge 处：
{pubkey ? (
  <span class="pubkey-badge" title={pubkey}>
    ⚡ {hexToNpub(pubkey).slice(0, 12)}…
  </span>
) : ...}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/Navbar.jsx
git commit -m "$(cat <<'EOF'
feat(web): Navbar badge shows npub format not hex

hexToNpub → npub1... prefix, 12-char truncation.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Relay 降级

**Files:**
- Modify: `web/src/lib/relay.js`

- [ ] **Step 1: 添加 relay 降级逻辑**

更新 `relay.js` 的 `connect` 函数：

```javascript
function connect() {
  return new Promise((resolve, reject) => {
    if (currentRelayIndex >= RELAYS.length) {
      reject(new Error('All relays failed'));
      return;
    }
    const relayUrl = RELAYS[currentRelayIndex];
    ws = new WebSocket(relayUrl);

    ws.onopen = () => resolve();
    ws.onerror = () => {
      ws.close();
      if (currentRelayIndex < RELAYS.length - 1) {
        currentRelayIndex++;
        connect().then(resolve).catch(reject);
      } else {
        reject(new Error('All relays failed'));
      }
    };
    // ... ws.onmessage unchanged
  });
}
```

在 `close()` 函数添加：
```javascript
currentRelayIndex = 0; // reset on close for clean reconnect
```

- [ ] **Step 2: 提交**

```bash
git add web/src/lib/relay.js
git commit -m "$(cat <<'EOF'
feat(web): relay fallback — sequential retry on relay failure

relay.nostr.band → nos.lol → relay.damus.io.
currentRelayIndex reset on close().

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: 添加单元测试

**Files:**
- Create: `web/src/__tests__/nostr.test.js`

- [ ] **Step 1: 添加 nostr.js 测试**

```javascript
import { describe, it, expect } from 'vitest';
import { hexToNpub, npubToHex } from '../lib/nostr.js';

describe('hexToNpub / npubToHex', () => {
  it('hexToNpub starts with npub1', () => {
    const result = hexToNpub('a'.repeat(64));
    expect(result.startsWith('npub1')).toBe(true);
  });

  it('round-trip: npubToHex(hexToNpub(hex)) === hex', () => {
    const hex = 'a'.repeat(64);
    const npub = hexToNpub(hex);
    expect(npubToHex(npub)).toBe(hex);
  });

  it('known test vector', () => {
    // hex of alice pubkey
    const hex = 'fda1a1a89f65b24c2b8c2f7f8a8e7d6c5b4a3928f6e7d8c9b0a1f2e3d4c5b6a';
    const npub = hexToNpub(hex.padEnd(64, '0'));
    expect(npub.startsWith('npub1')).toBe(true);
  });

  it('invalid npub throws', () => {
    expect(() => npubToHex('notnpub1xxxxx')).toThrow();
  });
});
```

- [ ] **Step 2: 运行测试**

```bash
cd /home/deeptuuk/Code3/AgentBoss/web && npm run test:run
```

- [ ] **Step 3: 提交**

```bash
git add web/src/__tests__/nostr.test.js
git commit -m "$(cat <<'EOF'
test: add nostr bech32 unit tests — round-trip, known vectors, errors

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 推送并提 PR

```bash
git push
gh pr create \
  --repo nicholasyangyang/AgentBoss \
  --title "feat(web): npub bech32 encoding + relay fallback (#31)" \
  --body "$(cat <<'EOF'
## Summary

Fix two production reliability issues from code review.

## Changes

- `web/src/lib/nostr.js`: Pure-JS bech32 npub encoding — `hexToNpub` / `npubToHex`
- `web/src/components/Navbar.jsx`: Badge shows `npub1...` format instead of hex
- `web/src/lib/relay.js`: Sequential relay fallback on failure
- `web/src/__tests__/nostr.test.js`: 4 test cases for bech32 round-trip

## Verification

- [ ] `hexToNpub` → starts with `npub1`
- [ ] `npubToHex(hexToNpub(hex)) === hex` round-trip passes
- [ ] Navbar badge shows npub format
- [ ] `npm test` passes

Closes #31.
EOF
)"
```

---

## 注意事项

- bech32 实现参考 bip-0173 标准，无需引入任何 npm 包
- `BECH32M_CONST = 0x2bc830a3` 用于 bech32m 校验和（npub/note 格式）
- `currentRelayIndex` 在 `close()` 时重置，确保重新连接从头开始
