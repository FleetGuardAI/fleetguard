import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { login, getCurrentUser, requestOtp, verifyOtp as verifyOtpApi } from '@/api/authApi';
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

  const msg91Handlers = useRef({
    onSuccess: null,
    onFailure: null
  });

  useEffect(() => {
    const initMsg91 = () => {
      console.log('[MSG91 DEBUG] initializing');
      if (window.initSendOTP && !window.msg91Initialized) {
        const configuration = {
          widgetId: import.meta.env.VITE_MSG91_WIDGET_ID,
          widget: import.meta.env.VITE_MSG91_WIDGET_ID,
          tokenAuth: import.meta.env.VITE_MSG91_WIDGET_TOKEN,
          identifier: "identifier",
          exposeMethods: true,
          success: (data) => {
            console.log('[MSG91 DEBUG] success callback fired');
            console.log('[MSG91 DEBUG] success callback data:', data);
            if (msg91Handlers.current.onSuccess) {
              msg91Handlers.current.onSuccess(data);
            }
          },
          failure: (error) => {
            console.log('[MSG91 DEBUG] failure callback fired');
            console.log('[MSG91 DEBUG] failure data:', error);
            if (msg91Handlers.current.onFailure) {
              msg91Handlers.current.onFailure(error);
            }
          }
        };

        console.log('[MSG91 DEBUG] initialized', {
          widgetConfigured: Boolean(configuration.widget),
          tokenConfigured: Boolean(configuration.tokenAuth),
          successCallback: typeof configuration.success,
          failureCallback: typeof configuration.failure,
        });

        window.initSendOTP(configuration);
        window.msg91Initialized = true;
      }
    };
    
    const scriptTimer = setInterval(() => {
      if (window.initSendOTP) {
        initMsg91();
        clearInterval(scriptTimer);
      }
    }, 500);
    return () => clearInterval(scriptTimer);
  }, []);

  const formatMobileForMsg91 = (num) => {
    let cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return '91' + cleaned;
    return cleaned;
  };

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
    
    const isEmail = email.includes('@');
    
    if (!isEmail) {
      if (!window.sendOtp) {
         setLoading(false);
         error('OTP Request Failed', 'MSG91 Web SDK is not loaded. Please disable adblockers or refresh.');
         return;
      }
      console.log('[AUTH DEBUG] web OTP flow started');
      console.log('[AUTH DEBUG] calling MSG91 sendOtp');
      const formattedMobile = formatMobileForMsg91(email);
      
      msg91Handlers.current.onSuccess = (data) => {
        console.log('[AUTH DEBUG] showing OTP input');
        setLoading(false);
        success('OTP Sent', 'A verification code has been sent to your mobile.');
        setOtpStep(2);
        setCountdown(60);
        setErrors({});
        setReqId('msg91-widget');
      };
      
      msg91Handlers.current.onFailure = (errData) => {
        setLoading(false);
        error('OTP Request Failed', errData?.message || 'Could not send OTP.');
      };

      try {
        const result = window.sendOtp(formattedMobile);
        if (result && typeof result.then === 'function') {
           result.then((data) => {
             console.log('[AUTH DEBUG] MSG91 sendOtp resolved');
             if (msg91Handlers.current.onSuccess) msg91Handlers.current.onSuccess(data);
           }).catch((err) => {
             if (msg91Handlers.current.onFailure) msg91Handlers.current.onFailure(err);
           });
        }
      } catch (err) {
        setLoading(false);
        error('OTP Request Failed', err.message || 'Error calling sendOtp.');
      }
      return;
    }

    
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
    
    if (!reqId) {
      success('OTP Sent', 'A verification code has been sent.');
      setCountdown(60);
      return;
    }

    setLoading(true);
    
    const isEmail = email.includes('@');
    if (!isEmail && reqId === 'msg91-widget') {
      if (!window.retryOtp) {
         setLoading(false);
         error('OTP Resend Failed', 'MSG91 Web SDK is not loaded.');
         return;
      }
      const formattedMobile = formatMobileForMsg91(email);
      
      msg91Handlers.current.onSuccess = (data) => {
        setLoading(false);
        success('OTP Resent', 'A new verification code has been sent.');
        setCountdown(60);
      };
      
      msg91Handlers.current.onFailure = (errData) => {
        setLoading(false);
        error('OTP Resend Failed', errData?.message || 'Could not resend OTP.');
      };

      try {
        const result = window.retryOtp(formattedMobile);
        if (result && typeof result.then === 'function') {
           result.then((data) => {
             if (msg91Handlers.current.onSuccess) msg91Handlers.current.onSuccess(data);
           }).catch((err) => {
             if (msg91Handlers.current.onFailure) msg91Handlers.current.onFailure(err);
           });
        }
      } catch (err) {
        setLoading(false);
        error('OTP Resend Failed', err.message || 'Error calling retryOtp.');
      }
      return;
    }
    
    try {
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
    
    const isEmail = email.includes('@');
    if (!isEmail && reqId === 'msg91-widget') {
      if (!window.verifyOtp) {
         setLoading(false);
         error('OTP Verification Failed', 'MSG91 Web SDK is not loaded.');
         return;
      }
      console.log('[AUTH DEBUG] MSG91 verifyOtp called');
      const formattedMobile = formatMobileForMsg91(email);
      
      msg91Handlers.current.onSuccess = async (data) => {
        console.log('[AUTH DEBUG] MSG91 verification resolved');
        let msg91Token = data;
        if (data && typeof data === 'object' && data.message) {
           msg91Token = data.message;
        }
        
        try {
          console.log('[AUTH DEBUG] sending msg91_token to FleetGuard');
          const res = await verifyOtpApi(email, null, null, { rememberMe, msg91Token });
          console.log('[AUTH DEBUG] FleetGuard verification response received');
          success('Login Successful', `Welcome back, ${res.user.name}!`);
          navigate('/dashboard');
        } catch (err) {
          setLoading(false);
          error('OTP Verification Failed', err.message || 'Invalid OTP.');
        }
      };

      msg91Handlers.current.onFailure = (errData) => {
        setLoading(false);
        error('OTP Verification Failed', errData?.message || 'Invalid OTP.');
      };

      try {
        const result = window.verifyOtp(formattedMobile, otpCode);
        if (result && typeof result.then === 'function') {
           result.then((data) => {
             if (msg91Handlers.current.onSuccess) msg91Handlers.current.onSuccess(data);
           }).catch((err) => {
             if (msg91Handlers.current.onFailure) msg91Handlers.current.onFailure(err);
           });
        }
      } catch (err) {
        setLoading(false);
        error('OTP Verification Failed', err.message || 'Error calling verifyOtp.');
      }
      return;
    }
    
    try {
      const res = await verifyOtpApi(email, reqId || "null_req", otpCode, { rememberMe });
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
