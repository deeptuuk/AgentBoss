import { useState } from 'preact/hooks';
import { signEvent } from '../lib/nostr.js';
import { createRelayClient, generateDTag } from '../lib/relay.js';
import { t } from '../lib/i18n.js';

export function PublishForm({ onClose, onSuccess }) {
  const [form, setForm] = useState({
    title: '',
    company: '',
    salary: '',
    province: '',
    city: '',
    description: '',
    contact: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!form.title.trim()) return setError(t('err_title'));
    if (!form.company.trim()) return setError(t('err_company'));
    if (!form.province.trim()) return setError(t('err_province'));
    if (!form.city.trim()) return setError(t('err_city'));

    setSubmitting(true);

    try {
      const dTag = generateDTag();
      const event = {
        kind: 30078,
        pubkey: '', // Will be filled by signer
        created_at: Math.floor(Date.now() / 1000),
        tags: [
          ['d', dTag],
          ['t', 'agentboss'],
          ['t', 'job'],
        ],
        content: JSON.stringify({
          title: form.title.trim(),
          company: form.company.trim(),
          salary_range: form.salary.trim(),
          description: form.description.trim(),
          contact: form.contact.trim(),
        }),
      };

      const signed = await signEvent(event);

      const relay = createRelayClient();
      await relay.connect();
      await relay.publish(signed);
      relay.close();

      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (err) {
      if (err.name === 'NoSignerError') {
        setError(t('err_nip07'));
      } else {
        setError(t('err_post'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div class="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose && onClose()}>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="publish-title">
        <div class="modal-header">
          <h2 class="modal-title" id="publish-title">{t('form_title')}</h2>
          <button class="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        {error && (
          <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 12px; margin-bottom: 20px; color: #fca5a5; font-size: 13px;">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="title">{t('form_title_label')}</label>
              <input
                id="title"
                class="form-input"
                type="text"
                placeholder={t('form_title_ph')}
                value={form.title}
                onInput={handleChange('title')}
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label" for="company">{t('form_company_label')}</label>
              <input
                id="company"
                class="form-input"
                type="text"
                placeholder={t('form_company_ph')}
                value={form.company}
                onInput={handleChange('company')}
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="province">{t('form_province_label')}</label>
              <input
                id="province"
                class="form-input"
                type="text"
                placeholder={t('form_province_ph')}
                value={form.province}
                onInput={handleChange('province')}
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label" for="city">{t('form_city_label')}</label>
              <input
                id="city"
                class="form-input"
                type="text"
                placeholder={t('form_city_ph')}
                value={form.city}
                onInput={handleChange('city')}
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="salary">{t('form_salary_label')}</label>
            <input
              id="salary"
              class="form-input"
              type="text"
              placeholder={t('form_salary_ph')}
              value={form.salary}
              onInput={handleChange('salary')}
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="description">{t('form_desc_label')}</label>
            <textarea
              id="description"
              class="form-textarea"
              placeholder={t('form_desc_ph')}
              value={form.description}
              onInput={handleChange('description')}
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="contact">{t('form_contact_label')}</label>
            <input
              id="contact"
              class="form-input"
              type="text"
              placeholder={t('form_contact_ph')}
              value={form.contact}
              onInput={handleChange('contact')}
            />
            <p class="form-hint">{t('form_contact_hint')}</p>
          </div>

          <button
            class="btn btn-primary form-submit"
            type="submit"
            disabled={submitting}
          >
            {submitting ? t('form_submit') : t('form_submit_btn')}
          </button>
        </form>
      </div>
    </div>
  );
}
