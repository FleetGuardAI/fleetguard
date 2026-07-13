import { mockUsers } from '@/data/mockData';

export async function login(email, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = mockUsers.find(u => u.email === email && u.status === 'active');
      if (user && password === 'admin') {
        localStorage.setItem('fleetguard_user', JSON.stringify(user));
        resolve({ success: true, user });
      } else if (email === 'coo@fleetguard.com' && password === 'admin') {
        const defaultUser = mockUsers[0];
        localStorage.setItem('fleetguard_user', JSON.stringify(defaultUser));
        resolve({ success: true, user: defaultUser });
      } else {
        reject(new Error('Invalid email or password.'));
      }
    }, 600);
  });
}

export async function logout() {
  return new Promise((resolve) => {
    setTimeout(() => {
      localStorage.removeItem('fleetguard_user');
      resolve({ success: true });
    }, 300);
  });
}

export async function getCurrentUser() {
  return new Promise((resolve) => {
    setTimeout(() => {
      const cached = localStorage.getItem('fleetguard_user');
      resolve(cached ? JSON.parse(cached) : null);
    }, 200);
  });
}
