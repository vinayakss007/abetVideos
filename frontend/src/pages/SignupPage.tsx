import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Video, UserPlus } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

function getStrength(password: string): { label: string; color: string; width: string } {
  let score = 0;
  if (password.length >= 6) score++;
  if (password.length >= 10) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  const levels = [
    { label: 'Weak', color: 'bg-red-500', width: 'w-1/5' },
    { label: 'Fair', color: 'bg-orange-500', width: 'w-2/5' },
    { label: 'Good', color: 'bg-yellow-500', width: 'w-3/5' },
    { label: 'Strong', color: 'bg-lime-500', width: 'w-4/5' },
    { label: 'Very Strong', color: 'bg-green-500', width: 'w-full' },
  ];
  return levels[Math.min(score, 4)];
}

export default function SignupPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      await signup({ email, password, full_name: fullName });
      toast.success('Account created!');
      navigate('/');
    } catch (err: unknown) {
      const ae = err as { response?: { data?: { detail?: string } } };
      const msg = ae.response?.data?.detail || 'Failed to create account';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const strength = password ? getStrength(password) : null;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-900">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-primary-600 rounded-xl mb-4">
            <Video className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">Create account</h1>
          <p className="text-gray-400 mt-1">Start creating AI videos</p>
        </div>
        <form onSubmit={handleSubmit} className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
              placeholder="At least 6 characters"
            />
            {strength && (
              <div className="mt-2">
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div className={`h-full ${strength.color} transition-all duration-300 ${strength.width}`} />
                </div>
                <p className={`text-xs mt-1 ${strength.color.replace('bg-', 'text-').replace('-500', '-400')}`}>
                  {strength.label}
                </p>
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Confirm Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500 ${
                confirmPassword && password !== confirmPassword ? 'border-red-500' : 'border-gray-600'
              }`}
              placeholder="Repeat your password"
            />
            {confirmPassword && password !== confirmPassword && (
              <p className="text-xs text-red-400 mt-1">Passwords do not match</p>
            )}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors font-medium text-sm"
          >
            <UserPlus className="w-4 h-4" />
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
          <p className="text-center text-sm text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
