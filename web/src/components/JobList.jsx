import { JobCard } from './JobCard.jsx';
import { t } from '../lib/i18n.js';

export function JobList({ jobs, loading, error, onJobClick, onRetry, onPublish }) {
  if (loading) {
    return (
      <div class="jobs-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} class="skeleton job-card-skeleton" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div class="empty-state">
        <div class="empty-state-icon">⚠</div>
        <h3>{t('load_error')}</h3>
        <p>{error}</p>
        {onRetry && (
          <button class="btn btn-secondary" onClick={onRetry}>
            {t('retry')}
          </button>
        )}
      </div>
    );
  }

  if (!jobs.length) {
    return (
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <h3>{t('empty_jobs')}</h3>
        <p>{t('empty_sub')}</p>
        {onPublish && (
          <button class="btn btn-primary" onClick={onPublish}>
            {t('publish_btn')}
          </button>
        )}
      </div>
    );
  }

  return (
    <div class="jobs-grid">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onClick={onJobClick} />
      ))}
    </div>
  );
}
