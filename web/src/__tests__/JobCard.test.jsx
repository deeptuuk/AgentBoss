import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { fireEvent } from '@testing-library/preact';
import { JobCard } from '../components/JobCard.jsx';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn().mockReturnValue('[]'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

const mockJob = {
  id: 'job1',
  title: '高级前端工程师',
  company: 'Nostr Labs',
  province: 'beijing',
  salary: '30k-50k',
  created_at: Math.floor(Date.now() / 1000) - 3600,
  pubkey: 'a'.repeat(64),
};

describe('JobCard', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockReturnValue('[]');
    localStorageMock.setItem.mockClear();
  });

  it('renders title and company', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('高级前端工程师')).toBeDefined();
    expect(screen.getByText('Nostr Labs')).toBeDefined();
  });

  it('renders province and salary tags', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText(/beijing/)).toBeDefined();
    expect(screen.getByText(/30k-50k/)).toBeDefined();
  });

  it('hides tags when province/salary absent', () => {
    const job = { ...mockJob, province: '', salary: '' };
    render(<JobCard job={job} />);
    expect(screen.queryByText(/beijing/)).toBeNull();
    expect(screen.queryByText(/30k-50k/)).toBeNull();
  });

  it('shows ☆ when not favorited', () => {
    render(<JobCard job={mockJob} />);
    const btn = screen.getByRole('button');
    expect(btn.innerHTML).toContain('☆');
  });

  it('shows ★ when already favorited', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify(['job1']));
    render(<JobCard job={mockJob} />);
    const btn = screen.getByRole('button');
    expect(btn.innerHTML).toContain('★');
  });

  it('toggles favorite on click', () => {
    render(<JobCard job={mockJob} />);
    fireEvent.click(screen.getByRole('button'));
    expect(localStorageMock.setItem).toHaveBeenCalled();
  });

  it('renders timeAgo output', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText(/分钟前|小时前/)).toBeDefined();
  });
});
