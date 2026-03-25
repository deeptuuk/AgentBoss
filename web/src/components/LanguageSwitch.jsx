import { getLang, setLang } from '../lib/i18n.js';

export function LanguageSwitch() {
  const lang = getLang();

  const toggle = () => setLang(lang === 'zh' ? 'en' : 'zh');

  return (
    <button
      class="lang-switch"
      onClick={toggle}
      title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      <span class={lang === 'zh' ? 'lang-active' : 'lang-inactive'}>ZH</span>
      <span class="lang-sep">|</span>
      <span class={lang === 'en' ? 'lang-active' : 'lang-inactive'}>EN</span>
    </button>
  );
}
