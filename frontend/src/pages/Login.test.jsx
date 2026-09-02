import { renderWithMemoryRouter, screen, waitFor } from '../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import Login from './Login';
import * as authApi from '../api/authApi';
import { fireEvent } from '@testing-library/react';

// Mock the API module
vi.mock('../api/authApi', () => ({
  login: vi.fn(),
  requestOtp: vi.fn(),
  verifyOtp: vi.fn(),
  getCurrentUser: vi.fn().mockResolvedValue(null),
}));

describe('Login Component', () => {
  it('renders login form correctly', () => {
    renderWithMemoryRouter(<Login />, { initialEntries: ['/login'] });
    expect(screen.getByLabelText(/Email or Mobile Number/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/)).toBeInTheDocument();
  });

  it('calls login api when submitting form', async () => {
    authApi.login.mockResolvedValue({ token: { access_token: 'fake_token' }, user: { full_name: 'Admin' } });
    
    renderWithMemoryRouter(<Login />, { initialEntries: ['/login'] });
    
    fireEvent.change(screen.getByLabelText(/Email or Mobile Number/i), { target: { value: 'admin@fleetguard.com' } });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith('admin@fleetguard.com', 'password123', expect.any(Object));
    });
  });
});
