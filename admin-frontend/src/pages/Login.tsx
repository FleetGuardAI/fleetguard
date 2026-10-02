import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../AuthContext';
import api, { getApiErrorMessage } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/auth/login', {
        email: email,
        password: password
      });
      
      login(response.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      console.error("Login request failed", {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url
      });
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md border border-slate-200">
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img src="/assets/the_vahan_logo.png" alt="Vahan Logo" className="h-12 w-auto object-contain" />
          </div>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest">Operations Portal</h2>
        </div>
        
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-slate-700 text-sm font-semibold mb-1.5">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
              required 
            />
          </div>
          <div className="relative">
            <label className="block text-slate-700 text-sm font-semibold mb-1.5">Password</label>
            <input 
              type={showPassword ? "text" : "password"} 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow pr-12"
              required 
            />
            <button
              type="button"
              className="absolute right-4 top-[34px] text-slate-400 hover:text-slate-600 focus:outline-none transition-colors"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <button 
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl transition-colors shadow-sm"
          >
            Sign In to Admin
          </button>
          
          {import.meta.env.DEV && (
            <button 
              type="button"
              onClick={() => {
                login("test_admin_token_bypass");
                navigate('/dashboard');
              }}
              className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-3 px-4 rounded-xl transition-colors shadow-sm mt-3"
            >
              Skip Login (Test Mode)
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
