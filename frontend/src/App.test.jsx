import { renderWithMemoryRouter, screen } from './utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

describe('App Component', () => {
  it('renders without crashing', () => {
    // Mock intersection observer, often used by framer-motion/lucide
    const mockIntersectionObserver = vi.fn();
    mockIntersectionObserver.mockReturnValue({
      observe: () => null,
      unobserve: () => null,
      disconnect: () => null
    });
    window.IntersectionObserver = mockIntersectionObserver;

    renderWithMemoryRouter(<App />, { initialEntries: ['/'] });
    expect(true).toBe(true);
  });
});
