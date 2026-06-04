import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Video, Mail, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import apiClient from '../api/client';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await apiClient.post('/auth/forgot-password', { email });
      toast.success('Reset link sent if email exists');
      if (res.data?.reset_token) {
        setResetToken(res.data.reset_token);
      }
    } catch {
      toast.error('Failed to request reset');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-900">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-primary-600 rounded-xl mb-4">
            <Video className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">Reset Password</h1>
          <p className="text-gray-400 mt-1">Enter your email to receive a reset link</p>
        </div>
        <form onSubmit={handleSubmit} className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-4">
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
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors font-medium text-sm"
          >
            <Mail className="w-4 h-4" />
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
          {resetToken && (
            <div className="p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
              <p className="text-xs text-yellow-300 font-medium mb-1">Development Mode — Reset Token:</p>
              <p className="text-xs text-yellow-400 break-all font-mono">{resetToken}</p>
              <Link
                to={`/reset-password?token=${resetToken}`}
                className="mt-2 inline-block text-xs text-primary-400 hover:text-primary-300"
              >
                Click here to reset →
              </Link>
            </div>
          )}
          <p className="text-center text-sm text-gray-400">
            <Link to="/login" className="inline-flex items-center gap-1 text-primary-400 hover:text-primary-300">
              <ArrowLeft className="w-3 h-3" /> Back to login
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
