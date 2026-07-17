import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Building2, User, Phone, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { registerCompany } from '@/api/authApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';

export default function Register() {
  const [form, setForm] = useState({
    company_name: '',
    owner_name: '',
    mobile_number: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();
  const navigate = useNavigate();

  const setField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const validate = () => {
    const next = {};

    if (!form.company_name.trim()) next.company_name = 'Company name is required';
    if (!form.owner_name.trim()) next.owner_name = 'Owner name is required';

    if (!form.mobile_number.trim()) {
      next.mobile_number = 'Mobile number is required';
    } else if (!/^\+?[1-9]\d{9,14}$/.test(form.mobile_number.trim())) {
      next.mobile_number = 'Use a valid number (e.g. +919876543210)';
    }

    if (form.email && !/^\S+@\S+\.\S+$/.test(form.email)) {
      next.email = 'Invalid email address';
    }

    if (!form.password) {
      next.password = 'Password is required';
    } else if (form.password.length < 8) {
      next.password = 'Password must be at least 8 characters';
    }

    if (!form.confirm_password) {
      next.confirm_password = 'Confirm password is required';
    } else if (form.confirm_password !== form.password) {
      next.confirm_password = 'Passwords do not match';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const payload = {
        ...form,
        company_name: form.company_name.trim(),
        owner_name: form.owner_name.trim(),
        mobile_number: form.mobile_number.trim(),
        email: form.email.trim() || null,
      };

      const res = await registerCompany(payload, { rememberMe });
      success('Registration Successful', `Welcome, ${res.user.name}!`);
      navigate('/dashboard');
    } catch (err) {
      error('Registration Failed', err.message || 'Unable to create account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden p-8 space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Create Fleet<span className="text-emerald-600">Guard</span> Account
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Register your company and primary admin access
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Company Name"
            type="text"
            placeholder="FleetGuard Logistics Ltd"
            value={form.company_name}
            onChange={(e) => setField('company_name', e.target.value)}
            error={errors.company_name}
            icon={<Building2 className="h-4 w-4" />}
            required
          />

          <Input
            label="Owner Name"
            type="text"
            placeholder="Rajesh Kumar"
            value={form.owner_name}
            onChange={(e) => setField('owner_name', e.target.value)}
            error={errors.owner_name}
            icon={<User className="h-4 w-4" />}
            required
          />

          <Input
            label="Mobile Number"
            type="text"
            placeholder="+919876543210"
            value={form.mobile_number}
            onChange={(e) => setField('mobile_number', e.target.value)}
            error={errors.mobile_number}
            icon={<Phone className="h-4 w-4" />}
            required
          />

          <Input
            label="Email (Optional)"
            type="email"
            placeholder="owner@fleetguard.com"
            value={form.email}
            onChange={(e) => setField('email', e.target.value)}
            error={errors.email}
            icon={<Mail className="h-4 w-4" />}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Minimum 8 characters"
              value={form.password}
              onChange={(e) => setField('password', e.target.value)}
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

            <Input
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Re-enter password"
              value={form.confirm_password}
              onChange={(e) => setField('confirm_password', e.target.value)}
              error={errors.confirm_password}
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
          </div>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                className="rounded border-slate-300 dark:border-slate-600 text-emerald-600 focus:ring-emerald-500/30"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Remember me on this device
            </label>
          </div>

          <Button
            type="submit"
            className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
            loading={loading}
          >
            Create Company Account
          </Button>
        </form>

        <div className="text-center text-xs text-slate-500 dark:text-slate-400">
          <p className="mb-2">
            Already have an account?{' '}
            <Link to="/login" className="text-emerald-600 hover:underline">
              Sign in
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
