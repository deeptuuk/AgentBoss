import { t } from '../lib/i18n.js';

export function DeleteModal({ job, onConfirm, onClose }) {
  return (
    <div class="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h2 class="modal-title">{t('delete_title')}</h2>
          <button class="modal-close" onClick={onClose}>×</button>
        </div>
        <div style="padding: 20px;">
          <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 14px;">
            {t('delete_confirm')}
          </p>
          <div style="display: flex; gap: 12px;">
            <button class="btn btn-secondary" onClick={onClose}>
              {t('cancel')}
            </button>
            <button class="btn btn-danger" onClick={onConfirm}>
              {t('delete_confirm_btn')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
