import React, { useState, useEffect } from 'react';
import { User, Shield, Key, History, Save, Laptop, Globe, LogOut } from 'lucide-react';
import { getCurrentUser } from '@/api/authApi';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';

export default function Profile() {
  const { success, error, info } = useToast();

  const [activeTab, setActiveTab] = useState('details'); // details, security, sessions
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Detail Form states
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [department, setDepartment] = useState('');
  const [savingDetails, setSavingDetails] = useState(false);
  const [detailsErrors, setDetailsErrors] = useState({});

  // Password Form states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState({});

  // Mock session list
  const [sessions, setSessions] = useState([
    { id: 1, device: 'Chrome / Windows 11', ip: '192.168.1.102', location: 'Jaipur, Rajasthan', current: true },
    { id: 2, device: 'Firefox / macOS Sequoia', ip: '103.22.45.18', location: 'Mumbai, Maharashtra', current: false }
  ]);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const u = await getCurrentUser();
        setUser(u);
        if (u) {
          setName(u.name);
          setPhone(u.mobile_number || u.phone || '+919999988888');
          setDepartment(u.department || 'Operations');
        }
      } catch (e) {
        error('Load Error', 'Failed to retrieve profile credentials.');
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  const handleSaveDetails = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!name.trim()) errs.name = 'Full name is required';
    if (!phone.trim()) errs.phone = 'Phone number is required';

    setDetailsErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSavingDetails(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      const updatedUser = { ...user, name: name.trim(), phone: phone.trim(), department };
      localStorage.setItem('fleetguard_user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      success('Profile Saved', 'Personal credentials updated successfully.');
    } catch (e) {
      error('Save Failed', 'Failed to update details.');
    } finally {
      setSavingDetails(false);
    }
  };

  const handleSavePassword = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!currentPassword) errs.currentPassword = 'Current password is required';
    
    if (!newPassword) {
      errs.newPassword = 'New password is required';
    } else if (newPassword.length < 8) {
      errs.newPassword = 'Password must contain at least 8 characters';
    }

    if (confirmPassword !== newPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }

    setPasswordErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSavingPassword(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      success('Password Updated', 'Your security password has been changed.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (e) {
      error('Update Failed', 'Failed to change password.');
    } finally {
      setSavingPassword(false);
    }
  };

  const handleRevokeSession = (id) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    info('Session Revoked', 'Logged out device successfully.');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (!user) {
    return (
      <Card className="p-6 text-center max-w-md mx-auto mt-12">
        <Shield className="h-12 w-12 text-content-muted mx-auto mb-3" />
        <h3 className="text-lg font-bold text-content">Access Restricted</h3>
        <p className="text-sm text-content-secondary mt-1">Please login to access your profile settings.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* User Header Profile Card */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row items-center gap-5">
          <div className="w-20 h-20 bg-brand-100 dark:bg-brand-900/30 text-brand-600 rounded-full flex items-center justify-center font-bold text-2xl border border-brand-200">
            {user.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div className="text-center sm:text-left space-y-1">
            <h1 className="text-2xl font-bold text-content">{user.name}</h1>
            <p className="text-sm text-content-secondary">{user.email}</p>
            {user.mobile_number && (
              <p className="text-xs text-content-secondary">Mobile: {user.mobile_number}</p>
            )}
            {user.company?.company_name && (
              <p className="text-xs text-content-secondary">Company: {user.company.company_name}</p>
            )}
            {user.company_id && (
              <p className="text-xs text-content-secondary">Company ID: {user.company_id}</p>
            )}
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
              <Badge variant="brand">{user.role}</Badge>
              <Badge variant={user.is_active ? 'success' : 'danger'}>
                {user.is_active ? 'Active Account' : 'Inactive Account'}
              </Badge>
              <Badge variant="neutral">{user.department}</Badge>
            </div>
            {user.last_login && (
              <p className="text-xs text-content-muted pt-1">
                Last login: {new Date(user.last_login).toLocaleString()}
              </p>
            )}
            {!user.last_login && (
              <p className="text-xs text-content-muted pt-1">Last login: not available</p>
            )}
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('details')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'details'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <User className="h-4 w-4" />
          Personal Details
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'security'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <Key className="h-4 w-4" />
          Security Credentials
        </button>
        <button
          onClick={() => setActiveTab('sessions')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'sessions'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <History className="h-4 w-4" />
          Active Sessions
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'details' && (
        <Card className="max-w-2xl">
          <CardHeader className="p-0 pb-4 border-b border-border mb-4">
            <CardTitle className="text-base">Personal Credentials Profile</CardTitle>
          </CardHeader>
          <form onSubmit={handleSaveDetails} className="space-y-4">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={detailsErrors.name}
              required
            />

            <Input
              label="WhatsApp Phone Contact"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              error={detailsErrors.phone}
              required
            />

            <Input
              label="Corporate Email Address"
              value={user.email}
              disabled
              className="bg-surface-secondary cursor-not-allowed text-content-muted"
            />

            <Input
              label="Department Section"
              value={department}
              disabled
              className="bg-surface-secondary cursor-not-allowed text-content-muted"
            />

            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                variant="primary"
                icon={<Save className="h-4 w-4" />}
                loading={savingDetails}
              >
                Save Details
              </Button>
            </div>
          </form>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card className="max-w-2xl">
          <CardHeader className="p-0 pb-4 border-b border-border mb-4">
            <CardTitle className="text-base">Change Password</CardTitle>
          </CardHeader>
          <form onSubmit={handleSavePassword} className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              error={passwordErrors.currentPassword}
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="New Password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                error={passwordErrors.newPassword}
                required
              />
              <Input
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                error={passwordErrors.confirmPassword}
                required
              />
            </div>

            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                variant="primary"
                icon={<Save className="h-4 w-4" />}
                loading={savingPassword}
              >
                Update Password
              </Button>
            </div>
          </form>
        </Card>
      )}

      {activeTab === 'sessions' && (
        <Card className="max-w-2xl space-y-4">
          <CardHeader className="p-0 pb-4 border-b border-border">
            <CardTitle className="text-base">Active Logged Devices</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-4 bg-surface border border-border rounded-xl gap-4 hover:border-brand-300 transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-surface-secondary text-content-secondary">
                    <Laptop className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-content flex items-center gap-2">
                      {session.device}
                      {session.current && (
                        <Badge variant="success" size="sm">Current</Badge>
                      )}
                    </h4>
                    <p className="text-xs text-content-secondary mt-0.5 flex items-center gap-1.5">
                      <Globe className="h-3.5 w-3.5" />
                      IP: {session.ip} • {session.location}
                    </p>
                  </div>
                </div>

                {!session.current && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-500 border-red-100 hover:bg-red-50"
                    icon={<LogOut className="h-3.5 w-3.5" />}
                    onClick={() => handleRevokeSession(session.id)}
                  >
                    Logout
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
