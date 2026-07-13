import { mockUsers, mockRoles, mockAuditLogs } from '@/data/mockData';

let localUsers = [...mockUsers];
let localRoles = [...mockRoles];
let localAuditLogs = [...mockAuditLogs];

export async function getSettings() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        companyName: 'FleetGuard Logistics Pvt Ltd',
        primaryContact: 'Suryansh Chaudhary',
        timezone: 'Asia/Kolkata (IST)',
        currency: 'INR (₹)',
        fuelTheftThresholdLiters: 18,
        speedLimitKmh: 80,
        smsAlertsEnabled: true,
        whatsappBotActive: true
      });
    }, 400);
  });
}

export async function saveSettings(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, updatedSettings: data });
    }, 500);
  });
}

// Admin: Users
export async function getAdminUsers() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(localUsers);
    }, 400);
  });
}

export async function addAdminUser(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newUser = {
        id: localUsers.length + 1,
        status: 'active',
        ...data
      };
      localUsers.push(newUser);
      resolve(newUser);
    }, 600);
  });
}

export async function toggleAdminUserStatus(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = localUsers.find(u => u.id === Number(id));
      if (user) {
        user.status = user.status === 'active' ? 'inactive' : 'active';
        resolve(user);
      } else {
        reject(new Error('User not found'));
      }
    }, 400);
  });
}

// Admin: Roles & Permissions
export async function getRolesMatrix() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(localRoles);
    }, 400);
  });
}

export async function updateRolePermissions(roleName, permissions) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const role = localRoles.find(r => r.role === roleName);
      if (role) {
        role.permissions = permissions;
        resolve(role);
      } else {
        reject(new Error('Role not found'));
      }
    }, 500);
  });
}

// Admin: Audit Logs
export async function getAuditLogs() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(localAuditLogs);
    }, 500);
  });
}

export async function addAuditLog(action, details) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const cached = localStorage.getItem('fleetguard_user');
      const currentUser = cached ? JSON.parse(cached) : { name: 'System' };
      const newLog = {
        id: `AUD-${Math.floor(1000 + Math.random() * 9000)}`,
        user: currentUser.name,
        action,
        details,
        timestamp: new Date().toISOString(),
        ip: '127.0.0.1'
      };
      localAuditLogs.unshift(newLog);
      resolve(newLog);
    }, 200);
  });
}
