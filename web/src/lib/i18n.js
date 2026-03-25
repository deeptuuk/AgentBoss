const STORAGE_KEY = 'agentboss_lang';

export const translations = {
  zh: {
    search_placeholder: '搜索职位、公司...',
    publish_btn: '+ 发布职位',
    signing: '签名中...',
    disconnected: '未连接',
    banner_text: 'Nostr 去中心化招聘',
    banner_sub: '开放 · 无需注册 · NIP-07 认证',
    hero_eyebrow: 'Nostr · 去中心化 · 开放',
    hero_title: '在 <em>Nostr</em> 上<br />发现下一个机会',
    hero_desc: 'AgentBoss 是基于 Nostr 协议的去中心化招聘平台。无需注册，无中心化平台，用你的 Nostr 公钥身份直接连接。',
    latest_jobs: '最新职位',
    loading_jobs: '加载中...',
    jobs_count: '个职位',
    data_overview: '数据概览',
    jobs: '职位',
    favorites: '收藏',
    popular_tags: '热门标签',
    need_nip07: '⚡ 需要 NIP-07 扩展',
    install_ext: '安装浏览器扩展来签名发布职位：',
    footer_text: 'AgentBoss · Nostr 去中心化招聘',
    github: 'GitHub',
    favorite: '收藏',
    unfavorite: '取消收藏',
    empty_jobs: '暂无职位',
    empty_sub: '成为第一个发布职位的人吧',
    load_error: '加载失败',
    form_title: '发布职位',
    form_title_label: '职位名称 *',
    form_title_ph: '如：高级前端工程师',
    form_company_label: '公司名称 *',
    form_company_ph: '如：Nostr Labs',
    form_province_label: '省份 *',
    form_province_ph: '如：beijing',
    form_city_label: '城市 *',
    form_city_ph: '如：beijing',
    form_salary_label: '薪资范围',
    form_salary_ph: '如：30k-50k',
    form_desc_label: '职位描述',
    form_desc_ph: '描述职位要求、职责...',
    form_contact_label: '联系方式',
    form_contact_ph: 'NIP-05 邮箱或其他联系方式',
    form_contact_hint: '可在 contact 字段填写您的 NIP-05（如 alice@nostr.com）',
    form_submit: '发布中...',
    form_submit_btn: '⚡ 发布到 Nostr',
    err_title: '请填写职位名称',
    err_company: '请填写公司名称',
    err_province: '请填写省份',
    err_city: '请填写城市',
    err_nip07: '请先安装 NIP-07 扩展（如 Alby）来签名发布',
    err_post: '发布失败，请重试',
    success: '✓ 职位已发布到 Nostr！',
    err_alert_nip07: '请先安装 NIP-07 扩展（如 Alby 或 nos2x）来发布职位',
    retry: '重试',
    contact: '联系方式',
  },
  en: {
    search_placeholder: 'Search jobs, companies...',
    publish_btn: '+ Post Job',
    signing: 'Signing...',
    disconnected: 'Not connected',
    banner_text: 'Nostr Decentralized Jobs',
    banner_sub: 'Open · No registration · NIP-07 Auth',
    hero_eyebrow: 'Nostr · Decentralized · Open',
    hero_title: 'Find Your Next Opportunity on <em>Nostr</em>',
    hero_desc: 'AgentBoss is a decentralized job platform on Nostr. No registration, no central authority — connect with your Nostr public key.',
    latest_jobs: 'Latest Jobs',
    loading_jobs: 'Loading...',
    jobs_count: 'jobs',
    data_overview: 'Stats',
    jobs: 'Jobs',
    favorites: 'Favorites',
    popular_tags: 'Popular Tags',
    need_nip07: '⚡ NIP-07 Extension Required',
    install_ext: 'Install a browser extension to sign and post jobs:',
    footer_text: 'AgentBoss · Nostr Decentralized Jobs',
    github: 'GitHub',
    favorite: 'Favorite',
    unfavorite: 'Unfavorite',
    empty_jobs: 'No jobs yet',
    empty_sub: 'Be the first to post a job',
    load_error: 'Failed to load',
    form_title: 'Post a Job',
    form_title_label: 'Job Title *',
    form_title_ph: 'e.g.: Senior Frontend Engineer',
    form_company_label: 'Company Name *',
    form_company_ph: 'e.g.: Nostr Labs',
    form_province_label: 'Province *',
    form_province_ph: 'e.g.: beijing',
    form_city_label: 'City *',
    form_city_ph: 'e.g.: beijing',
    form_salary_label: 'Salary Range',
    form_salary_ph: 'e.g.: 30k-50k',
    form_desc_label: 'Job Description',
    form_desc_ph: 'Describe requirements, responsibilities...',
    form_contact_label: 'Contact',
    form_contact_ph: 'NIP-05 email or other contact',
    form_contact_hint: 'Your NIP-05 (e.g. alice@nostr.com)',
    form_submit: 'Posting...',
    form_submit_btn: '⚡ Post to Nostr',
    err_title: 'Job title is required',
    err_company: 'Company name is required',
    err_province: 'Province is required',
    err_city: 'City is required',
    err_nip07: 'Please install a NIP-07 extension (e.g. Alby) to sign and post',
    err_post: 'Failed to post, please try again',
    success: '✓ Job posted to Nostr!',
    err_alert_nip07: 'Please install a NIP-07 extension (e.g. Alby or nos2x) to post',
    retry: 'Retry',
    contact: 'Contact',
  },
};

let _lang;
try {
  _lang = localStorage.getItem(STORAGE_KEY) || 'zh';
} catch {
  _lang = 'zh';
}

// subscribers notified on language change
const _subscribers = new Set();

export function t(key, params = {}) {
  let text = translations[_lang]?.[key] ?? key;
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, v);
  }
  return text;
}

export function getLang() {
  return _lang;
}

export function setLang(lang) {
  _lang = lang;
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // ignore storage errors
  }
  // notify all subscribers (triggers re-render in subscribed components)
  _subscribers.forEach((fn) => fn(lang));
}

export function subscribeToLang(fn) {
  _subscribers.add(fn);
  return () => _subscribers.delete(fn);
}
