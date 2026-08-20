import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { login, getCurrentUser, requestOtp, verifyOtp } from '@/api/authApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loginMethod, setLoginMethod] = useState('password'); // 'password' or 'otp'
  const [otpStep, setOtpStep] = useState(1); // 1 = enter identifier, 2 = enter otp
  const [otpCode, setOtpCode] = useState('');
  const [reqId, setReqId] = useState(null);
  const [errors, setErrors] = useState({});
  const { success, error } = useToast();
  const navigate = useNavigate();

  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    async function checkSession() {
      const user = await getCurrentUser();
      if (user) {
        navigate('/dashboard', { replace: true });
      }
    }
    checkSession();
  }, [navigate]);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [countdown]);

  const validate = () => {
    const newErrors = {};
    if (!email) {
      newErrors.email = 'Email or Mobile Number is required';
    } else {
      const isEmail = email.includes('@');
      if (isEmail) {
        if (!/\S+@\S+\.\S+/.test(email)) {
          newErrors.email = 'Invalid email address';
        }
      } else {
        // Allows digits and formats like E.164 (e.g. +919876543210 or 9876543210)
        if (!/^\+?[0-9\s-]{10,20}$/.test(email)) {
          newErrors.email = 'Invalid email or mobile number';
        }
      }
    }
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 4) {
      newErrors.password = 'Password must be at least 4 characters';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const res = await login(email, password, {
        rememberMe,
      });
      success('Login Successful', `Welcome back, ${res.user.name}!`);
      navigate('/dashboard');
    } catch (err) {
      error('Login Failed', err.message || 'Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    if (!email) {
      setErrors({ email: 'Email or Mobile Number is required' });
      return;
    }
    setLoading(true);
    try {
      const res = await requestOtp(email);
      success('OTP Sent', res.message);
      setReqId(res.req_id || null);
      setOtpStep(2);
      setCountdown(60);
      setErrors({});
    } catch (err) {
      error('OTP Request Failed', err.message || 'Could not send OTP.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (countdown > 0) return;
    
    // For non-existent users, we simulate success to avoid enumeration
    if (!reqId) {
      success('OTP Sent', 'A verification code has been sent.');
      setCountdown(60);
      return;
    }

    setLoading(true);
    try {
      // Need to import resendOtp from api/authApi
      const { resendOtp } = await import('@/api/authApi');
      const res = await resendOtp(reqId);
      success('OTP Resent', res.message || 'A new verification code has been sent.');
      setCountdown(60);
    } catch (err) {
      error('OTP Resend Failed', err.message || 'Could not resend OTP.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    if (!otpCode) {
      setErrors({ otp: 'OTP Code is required' });
      return;
    }
    setLoading(true);
    try {
      // If we don't have a reqId (null user case), the backend will fail it generically during verify or we can fail it
      // but to prevent enumeration, we just send null string or handle it
      const res = await verifyOtp(email, reqId || "null_req", otpCode, { rememberMe });
      success('Login Successful', `Welcome back, ${res.user.name}!`);
      navigate('/dashboard');
    } catch (err) {
      error('OTP Verification Failed', err.message || 'Invalid OTP.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-8 space-y-6">
        {/* Logo and Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 flex items-center justify-center">
            <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">
            Fleet<span className="text-emerald-600">Guard</span> ERP
          </h2>
          <p className="text-sm text-slate-500">
            Sign in to manage your trucking fleet
          </p>
        </div>


        {/* Login Method Toggle */}
        <div className="flex bg-slate-100 rounded-lg p-1">
          <button
            type="button"
            className={`flex-1 text-sm font-medium py-2 rounded-md transition-colors ${loginMethod === 'password' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => { setLoginMethod('password'); setErrors({}); }}
          >
            Password
          </button>
          <button
            type="button"
            className={`flex-1 text-sm font-medium py-2 rounded-md transition-colors ${loginMethod === 'otp' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => { setLoginMethod('otp'); setErrors({}); setOtpStep(1); setOtpCode(''); setReqId(null); }}
          >
            OTP
          </button>
        </div>

        {/* Login Form */}
        {loginMethod === 'password' ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <Input
              label="Email or Mobile Number"
              type="text"
              placeholder="coo@fleetguard.com or +919876543210"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              icon={<Mail className="h-4 w-4" />}
              required
            />

            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              icon={<Lock className="h-4 w-4" />}
              iconRight={
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="text-content-muted hover:text-content"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              required
            />

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-1.5 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/30"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                Remember me
              </label>
              <Link to="/forgot-password" className="text-emerald-600 hover:underline">
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
              loading={loading}
            >
              Sign In
            </Button>
          </form>
        ) : (
          <form onSubmit={otpStep === 1 ? handleRequestOtp : handleVerifyOtp} className="space-y-4">
            <Input
              label="Email or Mobile Number"
              type="text"
              placeholder="coo@fleetguard.com or +919876543210"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              icon={<Mail className="h-4 w-4" />}
              disabled={otpStep === 2}
              required
            />

            {otpStep === 2 && (
              <Input
                label="OTP Code"
                type="text"
                placeholder="123456"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                error={errors.otp}
                icon={<Lock className="h-4 w-4" />}
                required
              />
            )}

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-1.5 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/30"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                Remember me
              </label>
            </div>

            <Button
              type="submit"
              className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
              loading={loading}
            >
              {otpStep === 1 ? 'Request OTP' : 'Verify OTP'}
            </Button>

            {otpStep === 2 && (
              <div className="flex flex-col items-center mt-2 space-y-2">
                {countdown > 0 ? (
                  <span className="text-xs text-slate-500">
                    Resend OTP in {countdown}s
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={loading}
                    className="text-xs text-emerald-600 font-medium hover:underline disabled:opacity-50"
                  >
                    Resend OTP
                  </button>
                )}
                
                <button
                  type="button"
                  onClick={() => { setOtpStep(1); setOtpCode(''); }}
                  className="text-xs text-slate-500 hover:text-emerald-600 underline"
                >
                  Change Email / Mobile Number
                </button>
              </div>
            )}
          </form>
        )}

        <div className="text-center text-xs text-slate-500">
          <p className="mb-2">
            New company?{' '}
            <Link to="/register" className="text-emerald-600 hover:underline">
              Create your account
            </Link>
          </p>
          <Link to="/" className="hover:underline">
            Back to public landing page
          </Link>
        </div>
      </div>
    </div>
  );
}
