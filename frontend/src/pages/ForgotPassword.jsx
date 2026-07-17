import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { KeyRound, Shield, Mail, Lock, Ticket, Eye, EyeOff } from 'lucide-react';
import { requestPasswordReset, resetPassword } from '@/api/authApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';

export default function ForgotPassword() {
  const { success, error, info } = useToast();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loadingRequest, setLoadingRequest] = useState(false);
  const [loadingReset, setLoadingReset] = useState(false);
  const [errors, setErrors] = useState({});

  const validateRequest = () => {
    const next = {};
    if (!identifier.trim()) next.identifier = 'Email or mobile is required';
    setErrors((prev) => ({ ...prev, ...next }));
    return Object.keys(next).length === 0;
  };

  const validateReset = () => {
    const next = {};
    if (!resetToken.trim()) next.resetToken = 'Reset token is required';
    if (!newPassword) next.newPassword = 'New password is required';
    else if (newPassword.length < 8) next.newPassword = 'Password must be at least 8 characters';
    if (confirmPassword !== newPassword) next.confirmPassword = 'Passwords do not match';
    setErrors((prev) => ({ ...prev, ...next }));
    return Object.keys(next).length === 0;
  };

  const handleRequest = async (e) => {
    e.preventDefault();
    if (!validateRequest()) return;

    setLoadingRequest(true);
    try {
      const res = await requestPasswordReset(identifier.trim());
      success('Request Submitted', res.message);
      if (res.reset_token) {
        setResetToken(res.reset_token);
        info('Development Token Returned', 'A reset token was returned because backend DEBUG mode is enabled.');
      }
    } catch (err) {
      error('Request Failed', err.message || 'Could not create reset request.');
    } finally {
      setLoadingRequest(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    if (!validateReset()) return;

    setLoadingReset(true);
    try {
      const res = await resetPassword({
        reset_token: resetToken.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      success('Password Reset', res.message);
      navigate('/login');
    } catch (err) {
      error('Reset Failed', err.message || 'Could not reset password.');
    } finally {
      setLoadingReset(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl p-8 space-y-8">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Forgot <span className="text-emerald-600">Password</span>
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Request a reset token, then set a new password.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <form onSubmit={handleRequest} className="space-y-4 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">1. Request Reset</h3>

            <Input
              label="Email or Mobile"
              type="text"
              placeholder="owner@fleetguard.com or +919876543210"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              error={errors.identifier}
              icon={<Mail className="h-4 w-4" />}
              required
            />

            <Button
              type="submit"
              className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
              loading={loadingRequest}
              icon={<Ticket className="h-4 w-4" />}
            >
              Request Token
            </Button>
          </form>

          <form onSubmit={handleReset} className="space-y-4 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">2. Reset Password</h3>

            <Input
              label="Reset Token"
              type="text"
              placeholder="Paste reset token"
              value={resetToken}
              onChange={(e) => setResetToken(e.target.value)}
              error={errors.resetToken}
              icon={<KeyRound className="h-4 w-4" />}
              required
            />

            <Input
              label="New Password"
              type={showNewPassword ? 'text' : 'password'}
              placeholder="Minimum 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              error={errors.newPassword}
              icon={<Lock className="h-4 w-4" />}
              iconRight={
                <button
                  type="button"
                  onClick={() => setShowNewPassword((prev) => !prev)}
                  className="text-content-muted hover:text-content"
                  aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                >
                  {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              required
            />

            <Input
              label="Confirm New Password"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Re-enter new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={errors.confirmPassword}
              icon={<Lock className="h-4 w-4" />}
              iconRight={
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="text-content-muted hover:text-content"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              required
            />

            <Button
              type="submit"
              className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
              loading={loadingReset}
            >
              Update Password
            </Button>
          </form>
        </div>

        <div className="text-center text-xs text-slate-500 dark:text-slate-400">
          <Link to="/login" className="text-emerald-600 hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
