import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock matchMedia for window (often needed for responsive components like Recharts, Headless UI, etc.)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock HTMLCanvasElement for jsdom
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({ data: [] })),
  putImageData: vi.fn(),
  createImageData: vi.fn(),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn(),
}));

// Mock ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserverMock;

// Mock HTMLElement.scrollTo
window.HTMLElement.prototype.scrollTo = vi.fn();

// Mock IntersectionObserver
class IntersectionObserverMock {
  constructor(callback) {
    this.callback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.IntersectionObserver = IntersectionObserverMock;
global.IntersectionObserver = IntersectionObserverMock;

// Mock document.elementsFromPoint for jsdom
if (typeof document !== 'undefined' && !document.elementsFromPoint) {
  document.elementsFromPoint = vi.fn(() => []);
}

// Ensure localStorage is fully functional in jsdom environment
if (typeof window !== 'undefined') {
  const storage = {};
  const localStorageMock = {
    getItem: vi.fn((key) => storage[key] !== undefined ? storage[key] : null),
    setItem: vi.fn((key, value) => { storage[key] = String(value); }),
    removeItem: vi.fn((key) => { delete storage[key]; }),
    clear: vi.fn(() => { Object.keys(storage).forEach(k => delete storage[k]); }),
    key: vi.fn((idx) => Object.keys(storage)[idx] || null),
    get length() { return Object.keys(storage).length; }
  };
  Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });
}
