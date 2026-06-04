import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Video, Sparkles, Clock, Settings, LogOut, Home, Menu, X } from 'lucide-react';
import ConnectedSources from './ConnectedSources';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

const NAV_ITEMS = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/create', icon: Sparkles, label: 'Create' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:fixed inset-y-0 left-0 z-50 w-64 bg-gray-900/95 border-r border-gray-800 transform transition-transform duration-200 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:static lg:z-auto flex flex-col`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-gray-800 shrink-0">
          <Link to="/" className="flex items-center gap-2.5 group" onClick={() => setSidebarOpen(false)}>
            <div className="p-1.5 bg-primary-600 rounded-lg group-hover:bg-primary-500 transition-colors">
              <Video className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-primary-400 to-blue-400 bg-clip-text text-transparent">
              Abet Videos
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1 text-gray-500 hover:text-gray-300 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  active
                    ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 border border-transparent'
                }`}
              >
                <Icon className="w-5 h-5 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Connected sources */}
        {isAuthenticated && (
          <div className="border-t border-gray-800 shrink-0">
            <ConnectedSources />
          </div>
        )}

        {/* Bottom section */}
        <div className="p-3 border-t border-gray-800 shrink-0">
          {isAuthenticated ? (
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-800/50">
              <Link
                to="/profile"
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-2 min-w-0 flex-1"
              >
                <div className="w-7 h-7 rounded-full bg-primary-600/30 flex items-center justify-center shrink-0">
                  <span className="text-xs font-medium text-primary-400">
                    {(user?.full_name || user?.email || '?')[0].toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-300 truncate">{user?.full_name || user?.email}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="p-1.5 text-gray-500 hover:text-red-400 transition-colors shrink-0"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <Link
                to="/login"
                onClick={() => setSidebarOpen(false)}
                className="w-full px-3 py-2 text-center text-sm text-gray-400 hover:text-gray-200 rounded-lg hover:bg-gray-800/50 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/signup"
                onClick={() => setSidebarOpen(false)}
                className="w-full px-3 py-2 text-center text-sm bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors font-medium"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar (mobile hamburger) */}
        <header className="lg:hidden flex items-center justify-between h-14 px-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1.5 text-gray-400 hover:text-gray-200"
          >
            <Menu className="w-5 h-5" />
          </button>
          <Link to="/" className="flex items-center gap-2">
            <div className="p-1 bg-primary-600 rounded-lg">
              <Video className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-bold bg-gradient-to-r from-primary-400 to-blue-400 bg-clip-text text-transparent">
              Abet Videos
            </span>
          </Link>
          <div className="w-8" />
        </header>

        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
