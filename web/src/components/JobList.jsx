import { JobCard } from './JobCard.jsx';

export function JobList({ jobs, loading, error, onJobClick }) {
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
        <h3>加载失败</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!jobs.length) {
    return (
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <h3>暂无职位</h3>
        <p>成为第一个发布职位的人吧</p>
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
