import { useState, useEffect, useCallback } from 'preact/hooks';
import { createRelayClient, parseJobEvent, buildJobFilter } from '../lib/relay.js';

const FAVORITES_KEY = 'agentboss_favorites';

export function useJobs({ province, city, searchQuery } = {}) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJobs = useCallback(async () => {
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
        // Sort by created_at desc
        allJobs.sort((a, b) => b.created_at - a.created_at);

        // Filter by search query
        let filtered = allJobs;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          filtered = allJobs.filter(
            (j) =>
              j.title.toLowerCase().includes(q) ||
              j.company.toLowerCase().includes(q) ||
              j.description.toLowerCase().includes(q)
          );
        }

        setJobs(filtered);
        setLoading(false);
        relay.close();
      });

      relay.subscribe('jobs', buildJobFilter({ province, city }));
    } catch (err) {
      setError(err.message);
      setLoading(false);
      relay.close();
    }
  }, [province, city, searchQuery]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  return { jobs, loading, error, reload: loadJobs };
}
