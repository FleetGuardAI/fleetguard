/**
 * FleetGuard Authentication API Service
 * Integrates with FastAPI backend security layer.
 */

/**
 * Log in a user using email OR mobile number.
 * Stashes `fleetguard_token` and the mapped `fleetguard_user` in localStorage on success.
 *
 * @param {string} identifier - User's email address or mobile number
 * @param {string} password - User's plain password
 * @returns {Promise<{ success: boolean, user: object }>}
 */
export async function login(identifier, password) {
  const isEmail = identifier.includes('@');
  
  const payload = {
    password,
    email: isEmail ? identifier : null,
    mobile_number: !isEmail ? identifier : null,
  };

  const response = await fetch('/api/v1/auth/login', {
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

  const { access_token } = await response.json();
  localStorage.setItem('fleetguard_token', access_token);

  // Retrieve details of the authenticated user
  const user = await getCurrentUser();
  if (!user) {
    throw new Error('Authentication succeeded but user profile could not be retrieved.');
  }

  return { success: true, user };
}

/**
 * Log out of the system.
 * Clears the access token and user cache.
 */
export async function logout() {
  localStorage.removeItem('fleetguard_token');
  localStorage.removeItem('fleetguard_user');
  return { success: true };
}

/**
 * Fetch profile details of the active user session.
 * Re-validates the token with /api/v1/auth/me and updates cached info.
 *
 * @returns {Promise<object | null>} Mapped user profile object or null
 */
export async function getCurrentUser() {
  const token = localStorage.getItem('fleetguard_token');
  if (!token) return null;

  try {
    const response = await fetch('/api/v1/auth/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Clean up invalid or expired session
      localStorage.removeItem('fleetguard_token');
      localStorage.removeItem('fleetguard_user');
      return null;
    }

    const data = await response.json();
    const backendUser = data.user;

    // Map backend attributes to frontend expectations (name, role)
    const user = {
      ...backendUser,
      name: backendUser.full_name,
      role: backendUser.role,
    };

    localStorage.setItem('fleetguard_user', JSON.stringify(user));
    return user;
  } catch (err) {
    console.warn('[FleetGuard Auth] Failed to restore session from server:', err.message);
    const cached = localStorage.getItem('fleetguard_user');
    return cached ? JSON.parse(cached) : null;
  }
}
