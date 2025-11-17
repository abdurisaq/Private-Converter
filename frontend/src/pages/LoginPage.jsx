import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../utils/authStore';
import { authApi } from '../utils/api';
import toast from 'react-hot-toast';
import 'react-toastify/dist/ReactToastify.css';
import { Mail, Lock, Loader } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.login(email, password);
      const { access, refresh, user } = response; 
      setAuth(access, refresh, user);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Login failed');
      console.log("Login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="card max-w-md w-full mx-4 bg-gray-800 shadow-2xl border border-gray-700">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-purple-500 mb-2">FileFoundry</h1>
          <p className="text-gray-400">File Conversion Service</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 text-gray-500" size={20} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input pl-10 bg-gray-700 text-gray-100 border-gray-600 focus:ring-purple-500 focus:border-purple-500"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-gray-500" size={20} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input pl-10 bg-gray-700 text-gray-100 border-gray-600 focus:ring-purple-500 focus:border-purple-500"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 bg-purple-600 hover:bg-purple-700"
          >
            {loading && <Loader className="animate-spin" size={20} />}
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-700">
          <p className="text-center text-gray-400 text-sm">
            Don't have an account?{' '}
            <Link to="/register" className="text-purple-500 hover:text-purple-400 font-semibold">
              Register here
            </Link>
          </p>
        </div>

        <div className="mt-4 p-4 bg-gray-700 rounded-lg border border-gray-600">
          <p className="text-xs text-gray-400">
            <strong>Demo credentials:</strong><br />
            Email: demo@example.com<br />
            Password: demo123
          </p>
        </div>
      </div>
    </div>
  );
}
