/**
 * FleetGuard Authentication API Service
 * Integrates with FastAPI backend security layer.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

function formatApiError(detail, fallbackMessage) {
  if (!detail) return fallbackMessage;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(err => {
      const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : 'Field';
      return `${field}: ${err.msg}`;
    }).join(' | ');
  }
  if (typeof detail === 'object') {
    return detail.message || detail.error || fallbackMessage;
  }
  return fallbackMessage;
}

function getAuthStorage(rememberMe = true) {
  return rememberMe ? localStorage : sessionStorage;
}

function getTokenBundle() {
  const localToken = localStorage.getItem('fleetguard_token');
  if (localToken) {
    return {
      token: localToken,
      tokenType: localStorage.getItem('fleetguard_token_type') || 'bearer',
      rememberMe: true,
    };
  }

  const sessionToken = sessionStorage.getItem('fleetguard_token');
  if (sessionToken) {
    return {
      token: sessionToken,
      tokenType: sessionStorage.getItem('fleetguard_token_type') || 'bearer',
      rememberMe: false,
    };
  }

  return null;
}

function persistAuth(accessToken, tokenType = 'bearer', rememberMe = true) {
  const storage = getAuthStorage(rememberMe);
  storage.setItem('fleetguard_token', accessToken);
  storage.setItem('fleetguard_token_type', tokenType);
}

function persistUser(user, rememberMe = true) {
  const storage = getAuthStorage(rememberMe);
  storage.setItem('fleetguard_user', JSON.stringify(user));
}

function getCachedUser() {
  const local = localStorage.getItem('fleetguard_user');
  if (local) return JSON.parse(local);

  const session = sessionStorage.getItem('fleetguard_user');
  return session ? JSON.parse(session) : null;
}

function clearAuth() {
  localStorage.removeItem('fleetguard_token');
  localStorage.removeItem('fleetguard_token_type');
  localStorage.removeItem('fleetguard_user');

  sessionStorage.removeItem('fleetguard_token');
  sessionStorage.removeItem('fleetguard_token_type');
  sessionStorage.removeItem('fleetguard_user');
}

/**
 * Log in a user using email OR mobile number.
 * Stashes `fleetguard_token` and the mapped `fleetguard_user` in localStorage on success.
 *
 * @param {string} identifier - User's email address or mobile number
 * @param {string} password - User's plain password
 * @param {object} [options]
 * @param {boolean} [options.rememberMe=true]
 * @returns {Promise<{ success: boolean, user: object }>}
 */
export async function login(identifier, password, options = {}) {
  const { rememberMe = true } = options;
  const isEmail = identifier.includes('@');
  
  const payload = {
    password,
    email: isEmail ? identifier : null,
    mobile_number: !isEmail ? identifier : null,
    remember_me: rememberMe,
  };

  const response = await fetch(`${API_BASE}/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Authentication failed.' }));
    throw new Error(errorData.detail || 'Invalid credentials.');
  }

  const { access_token, token_type } = await response.json();
  clearAuth();
  persistAuth(access_token, token_type || 'bearer', rememberMe);

  // Retrieve details of the authenticated user
  const user = await getCurrentUser(rememberMe);
  if (!user) {
    throw new Error('Authentication succeeded but user profile could not be retrieved.');
  }

  return { success: true, user };
}

/**
 * Register a company and primary admin account.
 * Mirrors backend CompanyRegistrationRequest and stores token + user on success.
 *
 * @param {{ company_name: string, owner_name: string, mobile_number: string, email?: string, password: string, confirm_password: string }} payload
 * @param {object} [options]
 * @param {boolean} [options.rememberMe=true]
 * @returns {Promise<{ success: boolean, user: object }>}
 */
export async function registerCompany(payload, options = {}) {
  const { rememberMe = true } = options;
  const response = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Registration failed.' }));
    throw new Error(formatApiError(errorData.detail, 'Registration failed.'));
  }

  const data = await response.json();
  const token = data.token || {};

  if (token.access_token) {
    clearAuth();
    persistAuth(token.access_token, token.token_type || 'bearer', rememberMe);
  }

  const user = mapAuthUser({
    user: data.user,
    company: data.company,
    role: data.user?.role,
  });

  persistUser(user, rememberMe);
  return { success: true, user };
}

/**
 * Request password reset token by email or mobile identifier.
 *
 * @param {string} identifier
 * @returns {Promise<{ message: string, reset_token?: string, expires_at?: string }>} 
 */
export async function requestPasswordReset(identifier) {
  const response = await fetch(`${API_BASE}/v1/auth/forgot-password/request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      identifier,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Could not process request.' }));
    throw new Error(errorData.detail || 'Could not process request.');
  }

  return response.json();
}

/**
 * Reset password using one-time reset token.
 *
 * @param {{ reset_token: string, new_password: string, confirm_password: string }} payload
 * @returns {Promise<{ message: string }>}
 */
export async function resetPassword(payload) {
  const response = await fetch(`${API_BASE}/v1/auth/forgot-password/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Password reset failed.' }));
    throw new Error(errorData.detail || 'Password reset failed.');
  }

  return response.json();
}

/**
 * Log out of the system.
 * Clears the access token and user cache.
 */
export async function logout() {
  const tokenBundle = getTokenBundle();
  if (tokenBundle) {
    const { token, tokenType } = tokenBundle;
    try {
      await fetch(`${API_BASE}/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `${tokenType} ${token}`,
        },
      });
    } catch (e) {
      console.warn("Failed to logout from backend:", e);
    }
  }
  
  clearAuth();
  
  // Clear any cached data
  sessionStorage.clear();
  // We do not clear entirely localStorage here in case there are other non-auth prefs,
  // but clearing auth token effectively clears private data.
  // Optional: clear specific keys or localStorage.clear()
  
  return { success: true };
}

function mapAuthUser(data) {
  const backendUser = data?.user || {};
  const backendCompany = data?.company || null;

  return {
    ...backendUser,
    name: backendUser.full_name,
    phone: backendUser.mobile_number,
    mobile_number: backendUser.mobile_number,
    company_id: backendUser.company_id,
    is_active: backendUser.is_active,
    last_login: backendUser.last_login,
    role: data?.role || backendUser.role,
    company: backendCompany,
  };
}

/**
 * Fetch profile details of the active user session.
 * Re-validates the token with /api/v1/auth/me and updates cached info.
 *
 * @returns {Promise<object | null>} Mapped user profile object or null
 */
export async function getCurrentUser(preferredRememberMe = true) {
  const tokenBundle = getTokenBundle();
  if (!tokenBundle) return null;

  const { token, tokenType, rememberMe } = tokenBundle;

  try {
    const response = await fetch(`${API_BASE}/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `${tokenType} ${token}`,
      },
    });

    if (!response.ok) {
      // Clean up invalid or expired session
      clearAuth();
      return null;
    }

    const data = await response.json();
    const user = mapAuthUser(data);

    persistUser(user, rememberMe ?? preferredRememberMe);
    return user;
  } catch (err) {
    console.warn('[FleetGuard Auth] Failed to restore session from server:', err.message);
    return getCachedUser();
  }
}

/**
 * Update the details of the company for the active session.
 * 
 * @param {{ company_name?: string, owner_name?: string, mobile_number?: string, email?: string }} payload
 * @returns {Promise<{ success: boolean, user: object }>}
 */
export async function updateCompany(payload) {
  const tokenBundle = getTokenBundle();
  if (!tokenBundle) throw new Error('No active session.');

  const { token, tokenType, rememberMe } = tokenBundle;

  const response = await fetch(`${API_BASE}/v1/auth/company`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `${tokenType} ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to update company profile.' }));
    throw new Error(errorData.detail || 'Failed to update company profile.');
  }

  const data = await response.json();
  const user = mapAuthUser(data);

  persistUser(user, rememberMe);
  return { success: true, user };
}

export function getStoredUser() {
  return getCachedUser();
}

/**
 * Generate a short-lived QR token for Owner App pairing.
 */
export async function generateOwnerQR() {
  const tokenBundle = getTokenBundle();
  if (!tokenBundle) throw new Error('No active session.');

  const { token, tokenType } = tokenBundle;

  const response = await fetch(`${API_BASE}/v1/auth/owner-qr/generate`, {
    method: 'POST',
    headers: {
      'Authorization': `${tokenType} ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to generate QR token.' }));
    throw new Error(errorData.detail || 'Failed to generate QR token.');
  }

  return response.json();
}

/**
 * Request an OTP for login via identifier.
 */
export async function requestOtp(identifier) {
  const response = await fetch(`${API_BASE}/v1/auth/request-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ identifier }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to request OTP.' }));
    throw new Error(errorData.detail || 'Failed to request OTP.');
  }

  return response.json();
}

/**
 * Verify an OTP and receive an access token, storing it like a password login.
 */
export async function verifyOtp(identifier, req_id, code, options = {}) {
  const { rememberMe = true, msg91Token = null } = options;
  const response = await fetch(`${API_BASE}/v1/auth/verify-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
      identifier, 
      req_id: req_id || null, 
      code: code || null, 
      msg91_token: msg91Token 
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to verify OTP.' }));
    throw new Error(errorData.detail || 'Invalid or expired OTP.');
  }

  const { access_token, token_type } = await response.json();
  clearAuth();
  persistAuth(access_token, token_type || 'bearer', rememberMe);

  const user = await getCurrentUser(rememberMe);
  if (!user) {
    throw new Error('Authentication succeeded but user profile could not be retrieved.');
  }

  return { success: true, user };
}

/**
 * Resend an OTP.
 */
export async function resendOtp(req_id, channel = 'SMS') {
  const response = await fetch(`${API_BASE}/v1/auth/resend-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ req_id, channel }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to resend OTP.' }));
    throw new Error(errorData.detail || 'Failed to resend OTP.');
  }

  return response.json();
}
