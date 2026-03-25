import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { JobList } from '../components/JobList.jsx';

describe('JobList', () => {
  it('shows skeleton when loading', () => {
    render(<JobList jobs={[]} loading={true} error={null} />);
    // Skeleton renders 4 skeleton divs
    const skeletons = document.querySelectorAll('.job-card-skeleton');
    expect(skeletons.length).toBe(4);
  });

  it('shows error state', () => {
    render(<JobList jobs={[]} loading={false} error="网络错误" />);
    expect(screen.getByText('网络错误')).toBeDefined();
    expect(screen.getByText('加载失败')).toBeDefined();
  });

  it('shows empty state', () => {
    render(<JobList jobs={[]} loading={false} error={null} />);
    expect(screen.getByText('暂无职位')).toBeDefined();
  });

  it('renders job cards when jobs exist', () => {
    const mockJobs = [
      { id: '1', title: 'Job A', company: 'Corp A', created_at: Date.now() / 1000, pubkey: 'a'.repeat(64) },
      { id: '2', title: 'Job B', company: 'Corp B', created_at: Date.now() / 1000, pubkey: 'b'.repeat(64) },
    ];
    render(<JobList jobs={mockJobs} loading={false} error={null} />);
    const cards = document.querySelectorAll('.job-card');
    expect(cards.length).toBe(2);
  });
});
