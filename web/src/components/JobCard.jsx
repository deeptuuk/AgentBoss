import { useFavorites } from '../hooks/useFavorites.js';

function timeAgo(timestamp) {
  const seconds = Math.floor(Date.now() / 1000) - timestamp;
  if (seconds < 60) return '刚刚';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}天前`;
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN');
}

function shortPubkey(hex, len = 6) {
  if (!hex) return '';
  return `${hex.slice(0, len)}…`;
}

export function JobCard({ job, onClick }) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const fav = isFavorite(job.id);

  const handleFav = (e) => {
    e.stopPropagation();
    toggleFavorite(job.id);
  };

  return (
    <article class="job-card" onClick={() => onClick && onClick(job)}>
      <div class="job-card-header">
        <h3 class="job-title">{job.title}</h3>
        <button
          class={`job-favorite ${fav ? 'active' : ''}`}
          onClick={handleFav}
          title={fav ? '取消收藏' : '收藏'}
          aria-label={fav ? '取消收藏' : '收藏'}
        >
          {fav ? '★' : '☆'}
        </button>
      </div>

      <div class="job-company">
        <span>◆</span>
        {job.company}
      </div>

      <div class="job-tags">
        {job.province && (
          <span class="tag tag-region">
            🏙 {job.province}
          </span>
        )}
        {job.salary && (
          <span class="tag tag-salary">
            💰 {job.salary}
          </span>
        )}
      </div>

      <div class="job-meta">
        <span class="job-time">{timeAgo(job.created_at)}</span>
        <span class="job-author">
          ⚡ {shortPubkey(job.pubkey)}
        </span>
      </div>
    </article>
  );
}
