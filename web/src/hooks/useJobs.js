import { useState, useEffect, useCallback, useRef } from 'preact/hooks';
import { createRelayClient, parseJobEvent, buildJobFilter } from '../lib/relay.js';
import { useDeletedJobs } from './useDeletedJobs.js';

const FAVORITES_KEY = 'agentboss_favorites';

export function useJobs({ province, city, searchQuery } = {}) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const requestIdRef = useRef(0);
  const { isDeleted } = useDeletedJobs();

  const loadJobs = useCallback(async () => {
    const currentId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    const relay = createRelayClient();

    try {
      await relay.connect();

      const allJobs = [];
      relay.onEvent((event) => {
        const job = parseJobEvent(event);
        if (job) allJobs.push(job);
      });

      relay.onEOSE(() => {
        if (currentId !== requestIdRef.current) { relay.close(); return; }

        allJobs.sort((a, b) => b.created_at - a.created_at);

        let filtered = allJobs;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          filtered = filtered.filter(
            (j) =>
              j.title.toLowerCase().includes(q) ||
              j.company.toLowerCase().includes(q) ||
              j.description.toLowerCase().includes(q)
          );
        }
        filtered = filtered.filter((j) => !isDeleted(j.d_tag));

        setJobs(filtered);
        setLoading(false);
        relay.close();
      });

      relay.subscribe('jobs', buildJobFilter({ province, city }));
    } catch (err) {
      if (currentId !== requestIdRef.current) { relay.close(); return; }
      setError(err.message);
      setLoading(false);
      relay.close();
    }
  }, [province, city, searchQuery]);

  useEffect(() => {
    loadJobs();
    return () => {
      requestIdRef.current++;
    };
  }, [loadJobs]);

  return { jobs, loading, error, reload: loadJobs };
}
