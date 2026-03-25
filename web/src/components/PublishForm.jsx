import { useState } from 'preact/hooks';
import { signEvent } from '../lib/nostr.js';
import { createRelayClient, generateDTag } from '../lib/relay.js';

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

    if (!form.title.trim()) return setError('请填写职位名称');
    if (!form.company.trim()) return setError('请填写公司名称');
    if (!form.province.trim()) return setError('请填写省份');
    if (!form.city.trim()) return setError('请填写城市');

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

      // NIP-07 sign
      const signed = await signEvent(event);

      // Publish to relay
      const relay = createRelayClient();
      await relay.connect();
      await relay.publish(signed);
      relay.close();

      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (err) {
      if (err.name === 'NoSignerError') {
        setError('请先安装 NIP-07 扩展（如 Alby）来签名发布');
      } else {
        setError(err.message || '发布失败，请重试');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div class="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose && onClose()}>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="publish-title">
        <div class="modal-header">
          <h2 class="modal-title" id="publish-title">发布职位</h2>
          <button class="modal-close" onClick={onClose} aria-label="关闭">×</button>
        </div>

        {error && (
          <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 12px; margin-bottom: 20px; color: #fca5a5; font-size: 13px;">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="title">职位名称 *</label>
              <input
                id="title"
                class="form-input"
                type="text"
                placeholder="如：高级前端工程师"
                value={form.title}
                onInput={handleChange('title')}
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label" for="company">公司名称 *</label>
              <input
                id="company"
                class="form-input"
                type="text"
                placeholder="如：Nostr Labs"
                value={form.company}
                onInput={handleChange('company')}
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="province">省份 *</label>
              <input
                id="province"
                class="form-input"
                type="text"
                placeholder="如：beijing"
                value={form.province}
                onInput={handleChange('province')}
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label" for="city">城市 *</label>
              <input
                id="city"
                class="form-input"
                type="text"
                placeholder="如：beijing"
                value={form.city}
                onInput={handleChange('city')}
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="salary">薪资范围</label>
            <input
              id="salary"
              class="form-input"
              type="text"
              placeholder="如：30k-50k"
              value={form.salary}
              onInput={handleChange('salary')}
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="description">职位描述</label>
            <textarea
              id="description"
              class="form-textarea"
              placeholder="描述职位要求、职责..."
              value={form.description}
              onInput={handleChange('description')}
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="contact">联系方式</label>
            <input
              id="contact"
              class="form-input"
              type="text"
              placeholder="NIP-05 邮箱或其他联系方式"
              value={form.contact}
              onInput={handleChange('contact')}
            />
            <p class="form-hint">可在 contact 字段填写您的 NIP-05（如 alice@nostr.com）</p>
          </div>

          <button
            class="btn btn-primary form-submit"
            type="submit"
            disabled={submitting}
          >
            {submitting ? '发布中...' : '⚡ 发布到 Nostr'}
          </button>
        </form>
      </div>
    </div>
  );
}
