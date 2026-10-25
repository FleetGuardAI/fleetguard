import { renderWithMemoryRouter, screen } from './utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

describe('App Component', () => {
  it('renders without crashing', () => {
    // Mock intersection observer, often used by framer-motion/lucide
    class MockIntersectionObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    window.IntersectionObserver = MockIntersectionObserver;

    renderWithMemoryRouter(<App />, { initialEntries: ['/'] });
    expect(true).toBe(true);
  });
});
