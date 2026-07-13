import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock } from 'lucide-react';
import { login } from '@/api/authApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';

export default function Login() {
  const [email, setEmail] = useState('coo@fleetguard.com');
  const [password, setPassword] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const { success, error } = useToast();
  const navigate = useNavigate();

  const validate = () => {
    const newErrors = {};
    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Invalid email address';
    }
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 4) {
      newErrors.password = 'Password must be at least 4 characters';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const res = await login(email, password);
      success('Login Successful', `Welcome back, ${res.user.name}!`);
      navigate('/dashboard');
    } catch (err) {
      error('Login Failed', err.message || 'Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden p-8 space-y-6">
        {/* Logo and Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Fleet<span className="text-emerald-600">Guard</span> ERP
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Sign in to manage your trucking fleet
          </p>
        </div>

        {/* Credentials Tip Card */}
        <div className="p-3 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 rounded-lg">
          <p className="text-xs text-emerald-800 dark:text-emerald-400 font-medium">
            Demo Credentials:
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Email: <span className="font-mono">coo@fleetguard.com</span> / Pass: <span className="font-mono">admin</span>
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="coo@fleetguard.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            icon={<Mail className="h-4 w-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            icon={<Lock className="h-4 w-4" />}
            required
          />

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 cursor-pointer">
              <input type="checkbox" className="rounded border-slate-300 dark:border-slate-600 text-emerald-600 focus:ring-emerald-500/30" defaultChecked />
              Remember me
            </label>
            <a href="#" className="text-emerald-600 hover:text-emerald-700 font-medium">
              Forgot password?
            </a>
          </div>

          <Button
            type="submit"
            className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg"
            loading={loading}
          >
            Sign In
          </Button>
        </form>

        <div className="text-center text-xs text-slate-500 dark:text-slate-400">
          <Link to="/" className="hover:underline">
            Back to public landing page
          </Link>
        </div>
      </div>
    </div>
  );
}
