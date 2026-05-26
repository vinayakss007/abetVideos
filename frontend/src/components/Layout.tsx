import { Link, Outlet } from 'react-router-dom';
import { Video, Sparkles } from 'lucide-react';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="p-2 bg-primary-600 rounded-lg group-hover:bg-primary-500 transition-colors">
                <Video className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-400 to-blue-400 bg-clip-text text-transparent">
                Abet Videos
              </span>
            </Link>
            <nav className="flex items-center gap-4">
              <Link
                to="/create"
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors font-medium text-sm"
              >
                <Sparkles className="w-4 h-4" />
                Create Video
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-gray-800 bg-gray-900/50 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
          Abet Videos - AI-Powered Video Generation
        </div>
      </footer>
    </div>
  );
}
