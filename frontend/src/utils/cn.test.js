import { describe, it, expect } from 'vitest';
import { cn } from './cn';

describe('cn utility', () => {
  it('merges tailwind classes correctly', () => {
    expect(cn('p-4', 'p-8')).toBe('p-8');
    expect(cn('text-red-500', {'bg-blue-500': true, 'hidden': false})).toBe('text-red-500 bg-blue-500');
  });
});
