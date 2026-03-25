// Tracks d_tags of locally-deleted jobs in localStorage
const DELETED_KEY = 'agentboss_deleted_jobs';

function getDeleted() {
  try {
    return JSON.parse(localStorage.getItem(DELETED_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveDeleted(list) {
  localStorage.setItem(DELETED_KEY, JSON.stringify(list));
}

export function useDeletedJobs() {
  const isDeleted = (dTag) => getDeleted().includes(dTag);
  const markDeleted = (dTag) => {
    const list = getDeleted();
    if (!list.includes(dTag)) saveDeleted([...list, dTag]);
  };
  return { isDeleted, markDeleted };
}
