import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { KeyRound, Shield, Mail, Lock, Ticket, Eye, EyeOff, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
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
  const [requestStatus, setRequestStatus] = useState(null); // { message: string, requestId?: number }
  const [resetError, setResetError] = useState('');
  const [errors, setErrors] = useState({});

  const validateRequest = () => {
    const next = {};
    if (!identifier.trim()) next.identifier = 'Registered email or mobile is required';
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
    setErrors((prev) => ({ ...prev, identifier: undefined }));
    try {
      const res = await requestPasswordReset(identifier.trim());
      setRequestStatus({
        message: res.message || 'Password reset request submitted for Super Admin review.',
        requestId: res.request_id || null,
      });
      success('Request Submitted', 'Your reset request is awaiting Super Admin approval.');
      // Ensure resetToken is NEVER prefilled prior to admin issuance
      setResetToken('');
    } catch (err) {
      error('Request Failed', err.message || 'Could not submit reset request.');
    } finally {
      setLoadingRequest(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setResetError('');
    if (!validateReset()) return;

    setLoadingReset(true);
    try {
      const res = await resetPassword({
        identifier: identifier.trim() || undefined,
        reset_token: resetToken.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      success('Password Reset', res.message || 'Your password has been reset successfully.');
      // Clear sensitive fields to prevent accidental double submission
      setResetToken('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => {
        navigate('/login');
      }, 1200);
    } catch (err) {
      const msg = err.message || 'Reset failed. Token may be invalid, expired, or already used.';
      setResetError(msg);
      error('Reset Failed', msg);
    } finally {
      setLoadingReset(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-slate-200 shadow-xl p-8 space-y-8">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 flex items-center justify-center">
            <img src="/assets/the_vahan_logo.png" alt="the vahan Logo" className="w-full h-full object-contain" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">
            Forgot <span className="text-emerald-600">Password</span>
          </h2>
          <p className="text-sm text-slate-500">
            Submit a reset request for Super Admin authorization, then apply your unique token.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* LEFT SECTION: 1. REQUEST RESET */}
          <form onSubmit={handleRequest} className="space-y-4 border border-slate-200 rounded-xl p-4 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">1. Request Reset</h3>
                <span className="text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Admin Approval Required
                </span>
              </div>

              <p className="text-xs text-slate-500">
                Enter your registered email address or mobile number. A Super Admin will review your account and issue a secure reset token.
              </p>

              <Input
                label="Registered Email or Mobile"
                type="text"
                placeholder="e.g. fleetowner@thevahan.com"
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  if (errors.identifier) setErrors((prev) => ({ ...prev, identifier: undefined }));
                }}
                error={errors.identifier}
                icon={<Mail className="h-4 w-4" />}
                required
              />

              {requestStatus && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-800 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-900">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <span>Request Awaiting Approval</span>
                  </div>
                  <p className="text-emerald-700 leading-relaxed">
                    {requestStatus.message}
                  </p>
                  {requestStatus.requestId && (
                    <p className="text-[11px] text-emerald-600 font-mono mt-1">
                      Request Reference: #{requestStatus.requestId}
                    </p>
                  )}
                </div>
              )}
            </div>

            <Button
              type="submit"
              className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg mt-2"
              loading={loadingRequest}
              disabled={loadingRequest}
              icon={<Ticket className="h-4 w-4" />}
            >
              Request Token
            </Button>
          </form>

          {/* RIGHT SECTION: 2. RESET PASSWORD */}
          <form onSubmit={handleReset} className="space-y-4 border border-slate-200 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-900">2. Reset Password</h3>

            <p className="text-xs text-slate-500">
              Paste the single-use token received from your Super Admin, then choose a secure new password.
            </p>

            {resetError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                <span>{resetError}</span>
              </div>
            )}

            <Input
              label="Reset Token"
              type="text"
              placeholder="Paste token provided by administrator"
              value={resetToken}
              onChange={(e) => {
                setResetToken(e.target.value);
                if (errors.resetToken) setErrors((prev) => ({ ...prev, resetToken: undefined }));
                if (resetError) setResetError('');
              }}
              error={errors.resetToken}
              icon={<KeyRound className="h-4 w-4" />}
              required
            />

            <Input
              label="New Password"
              type={showNewPassword ? 'text' : 'password'}
              placeholder="Minimum 8 characters"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (errors.newPassword) setErrors((prev) => ({ ...prev, newPassword: undefined }));
              }}
              error={errors.newPassword}
              icon={<Lock className="h-4 w-4" />}
              iconRight={
                <button
                  type="button"
                  onClick={() => setShowNewPassword((prev) => !prev)}
                  className="text-slate-400 hover:text-slate-600 transition"
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
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (errors.confirmPassword) setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
              }}
              error={errors.confirmPassword}
              icon={<Lock className="h-4 w-4" />}
              iconRight={
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="text-slate-400 hover:text-slate-600 transition"
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
              disabled={loadingReset}
            >
              Update Password
            </Button>
          </form>
        </div>

        <div className="text-center text-xs text-slate-500">
          <Link to="/login" className="text-emerald-600 font-semibold hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
