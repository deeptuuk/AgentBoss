# AgentBoss 中英文切换 — 规格文档

**Author:** nicholasyangyang
**Date:** 2026-03-25
**Status:** Approved

---

## 1. 背景

Issue #27：网页增加中英文切换，界面需要有品味。

当前所有 UI 文本硬编码为中文，需支持简体中文 ↔ English。

## 2. 目标

- 顶部 Navbar 右侧显示语言切换器
- 点击切换 UI 语言，localStorage 记忆用户选择
- 刷新/重新访问保持上次选择
- 切换无刷新，纯前端实现

## 3. 设计决策

### 3.1 语言切换器外观

```
AgentBoss    [搜索...]    ZH | EN    + 发布职位
                     ↑ 当前语言带下划线
```

- 纯文字代码：`ZH` / `EN`，无国旗图标（俗）
- 当前语言加下划线指示，视觉上轻量、精确
- 字体：JetBrains Mono（与主题一致）
- 颜色：`var(--text-muted)`，hover 时高亮

### 3.2 翻译字典结构

```javascript
// web/src/lib/i18n.js
export const translations = {
  zh: { /* ... */ },
  en: { /* ... */ },
};

let _lang = localStorage.getItem('lang') || 'zh';

export function t(key) {
  return translations[_lang][key] ?? key;
}

export function setLang(lang) {
  _lang = lang;
  localStorage.setItem('lang', lang);
}

export function getLang() {
  return _lang;
}
```

### 3.3 翻译文本清单

| Key | ZH | EN |
|-----|----|----|
| search_placeholder | 搜索职位、公司... | Search jobs, companies... |
| publish_btn | + 发布职位 | + Post Job |
| signing | 签名中... | Signing... |
| disconnected | 未连接 | Not connected |
| banner_text | Nostr 去中心化招聘 | Nostr Decentralized Jobs |
| banner_sub | 开放 · 无需注册 · NIP-07 认证 | Open · No registration · NIP-07 Auth |
| hero_eyebrow | Nostr · 去中心化 · 开放 | Nostr · Decentralized · Open |
| hero_title | 在 Nostr 上发现下一个机会 | Find Your Next Opportunity on Nostr |
| hero_desc | AgentBoss 是基于 Nostr 协议的去中心化招聘平台。无需注册，无中心化平台，用你的 Nostr 公钥身份直接连接。 | AgentBoss is a decentralized job platform on Nostr. No registration, no central authority — connect with your Nostr public key. |
| latest_jobs | 最新职位 | Latest Jobs |
| loading_jobs | 加载中... | Loading... |
| jobs_count | {n} 个职位 | {n} jobs |
| data_overview | 数据概览 | Stats |
| jobs | 职位 | Jobs |
| favorites | 收藏 | Favorites |
| popular_tags | 热门标签 | Popular Tags |
| need_nip07 | ⚡ 需要 NIP-07 扩展 | ⚡ NIP-07 Extension Required |
| install_ext | 安装浏览器扩展来签名发布职位： | Install a browser extension to sign and post jobs: |
| footer_text | AgentBoss · Nostr 去中心化招聘 | AgentBoss · Nostr Decentralized Jobs |
| github | GitHub | GitHub |
| favorite | 收藏 | Favorite |
| unfavorite | 取消收藏 | Unfavorite |
| empty_jobs | 暂无职位 | No jobs yet |
| empty_sub | 成为第一个发布职位的人吧 | Be the first to post a job |
| load_error | 加载失败 | Failed to load |
| form_title | 发布职位 | Post a Job |
| form_title_label | 职位名称 * | Job Title * |
| form_title_ph | 如：高级前端工程师 | e.g.: Senior Frontend Engineer |
| form_company_label | 公司名称 * | Company Name * |
| form_company_ph | 如：Nostr Labs | e.g.: Nostr Labs |
| form_province_label | 省份 * | Province * |
| form_province_ph | 如：beijing | e.g.: beijing |
| form_city_label | 城市 * | City * |
| form_city_ph | 如：beijing | e.g.: beijing |
| form_salary_label | 薪资范围 | Salary Range |
| form_salary_ph | 如：30k-50k | e.g.: 30k-50k |
| form_desc_label | 职位描述 | Job Description |
| form_desc_ph | 描述职位要求、职责... | Describe requirements, responsibilities... |
| form_contact_label | 联系方式 | Contact |
| form_contact_ph | NIP-05 邮箱或其他联系方式 | NIP-05 email or other contact |
| form_contact_hint | 可在 contact 字段填写您的 NIP-05（如 alice@nostr.com） | Your NIP-05 (e.g. alice@nostr.com) |
| form_submit | 发布中... | Posting... |
| form_submit_btn | ⚡ 发布到 Nostr | ⚡ Post to Nostr |
| err_title | 请填写职位名称 | Job title is required |
| err_company | 请填写公司名称 | Company name is required |
| err_province | 请填写省份 | Province is required |
| err_city | 请填写城市 | City is required |
| err_nip07 | 请先安装 NIP-07 扩展（如 Alby）来签名发布 | Please install a NIP-07 extension (e.g. Alby) to sign and post |
| err_post | 发布失败，请重试 | Failed to post, please try again |
| success | ✓ 职位已发布到 Nostr！ | ✓ Job posted to Nostr! |

## 4. 文件变更

| 文件 | 变更 |
|------|------|
| `web/src/lib/i18n.js` | 新增 — 翻译字典 + t/getLang/setLang |
| `web/src/components/LanguageSwitch.jsx` | 新增 — ZH/EN 切换组件 |
| `web/src/components/Navbar.jsx` | 替换硬编码文本为 t()，添加 LanguageSwitch |
| `web/src/app.jsx` | 替换所有 UI 文本为 t() |
| `web/src/components/JobCard.jsx` | 替换收藏相关文本 |
| `web/src/components/JobList.jsx` | 替换加载/空状态/错误文本 |
| `web/src/components/PublishForm.jsx` | 替换所有表单文本 |

## 5. 不在本次范围

- 语言自动检测（浏览器语言）
- RTL 语言支持
- 日期/数字格式化
- relay 数据内容翻译
