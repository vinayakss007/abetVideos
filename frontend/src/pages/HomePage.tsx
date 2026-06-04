import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Video, Mic, Images, Clapperboard, Film, ArrowRight, AlertCircle, RotateCcw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getVideoHistory, getVideoDownloadUrl } from '../api/client';
import type { HistoryEntry } from '../types';

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI Script Generation',
    description: 'Enter a topic and get a professionally structured video script in seconds.',
  },
  {
    icon: Mic,
    title: 'Text-to-Speech',
    description: 'Convert your script narration to natural-sounding voice-over audio.',
  },
  {
    icon: Images,
    title: 'Smart Media Sourcing',
    description: 'Automatically find relevant images, GIFs, and stock footage for each scene.',
  },
  {
    icon: Clapperboard,
    title: 'Video Assembly',
    description: 'Combine everything into a polished video ready for sharing.',
  },
];

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const [recentVideos, setRecentVideos] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    getVideoHistory()
      .then((h) => { if (!cancelled) { setRecentVideos(h.slice(0, 4)); setLoading(false); } })
      .catch(() => { if (!cancelled) { setError('Failed to load recent videos'); setLoading(false); } });
    return () => { cancelled = true; };
  }, [isAuthenticated]);

  if (isAuthenticated) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome + Quick Create */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">Create and manage your AI-powered videos</p>
          </div>
          <Link
            to="/create"
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all text-sm shadow-lg shadow-primary-600/20"
          >
            <Sparkles className="w-4 h-4" />
            New Video
          </Link>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="p-5 bg-gray-900/50 border border-gray-800 rounded-xl">
            <Film className="w-5 h-5 text-primary-400 mb-2" />
            {loading ? (
              <div className="h-8 w-16 bg-gray-700 rounded animate-pulse mb-1" />
            ) : (
              <p className="text-2xl font-bold text-gray-100">{recentVideos.length}</p>
            )}
            <p className="text-xs text-gray-500">Videos Created</p>
          </div>
          <div className="p-5 bg-gray-900/50 border border-gray-800 rounded-xl">
            <Sparkles className="w-5 h-5 text-blue-400 mb-2" />
            <p className="text-2xl font-bold text-gray-100">AI</p>
            <p className="text-xs text-gray-500">Script + Voice + Media</p>
          </div>
          <div className="p-5 bg-gray-900/50 border border-gray-800 rounded-xl">
            <Video className="w-5 h-5 text-green-400 mb-2" />
            <p className="text-2xl font-bold text-gray-100">1-Click</p>
            <p className="text-xs text-gray-500">Full Video Generation</p>
          </div>
        </div>

        {/* Recent videos */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-200">Recent Videos</h2>
            {recentVideos.length > 0 && (
              <Link to="/history" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            )}
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-900/20 border border-red-700/50 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <p className="text-red-300 text-sm">{error}</p>
              </div>
              <button
                onClick={() => { setError(null); setLoading(true); getVideoHistory()
                  .then((h) => setRecentVideos(h.slice(0, 4)))
                  .catch(() => setError('Failed to load recent videos'))
                  .finally(() => setLoading(false)); }}
                className="flex items-center gap-1 px-3 py-1.5 bg-red-800/50 hover:bg-red-800 border border-red-700 rounded-lg text-red-300 text-sm transition-colors"
              >
                <RotateCcw className="w-3 h-3" /> Retry
              </button>
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
                  <div className="p-3 bg-gray-800 rounded-lg shrink-0">
                    <div className="w-5 h-5 bg-gray-700 rounded animate-pulse" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 bg-gray-700 rounded animate-pulse" />
                    <div className="h-3 w-1/2 bg-gray-700 rounded animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentVideos.length === 0 ? (
            <div className="text-center py-12 bg-gray-900/30 border border-gray-800 rounded-xl">
              <Film className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No videos yet</p>
              <p className="text-gray-600 text-sm mt-1">Create your first video to get started.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {recentVideos.map((v) => (
                <div
                  key={v.id}
                  className="flex items-center gap-4 p-4 bg-gray-900/50 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
                >
                  <div className="p-3 bg-gray-800 rounded-lg shrink-0">
                    <Film className="w-5 h-5 text-primary-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-200 truncate">{v.title}</p>
                    <p className="text-xs text-gray-500">
                      {v.scenes_count} scenes &middot; {Math.round(v.duration_seconds)}s
                    </p>
                  </div>
                  <a
                    href={getVideoDownloadUrl(v.video_id)}
                    download={`video-${v.video_id}.mp4`}
                    className="text-xs text-primary-400 hover:text-primary-300 shrink-0"
                  >
                    Download
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <section className="text-center py-16 sm:py-24">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-900/30 border border-primary-700/50 rounded-full text-primary-300 text-sm mb-6">
          <Video className="w-4 h-4" />
          AI-Powered Video Generation
        </div>
        <h1 className="text-4xl sm:text-6xl font-bold mb-6">
          <span className="bg-gradient-to-r from-primary-400 via-blue-400 to-primary-400 bg-clip-text text-transparent">
            Create Videos
          </span>
          <br />
          <span className="text-gray-100">with AI in Minutes</span>
        </h1>
        <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Transform any topic into an engaging video. AI writes the script, generates voice-over,
          finds visual media, and assembles everything into a finished video.
        </p>
        <Link
          to="/create"
          className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all text-lg shadow-lg shadow-primary-600/25"
        >
          <Sparkles className="w-5 h-5" />
          Create Your First Video
        </Link>
      </section>

      <section className="py-16">
        <h2 className="text-2xl font-bold text-center text-gray-100 mb-12">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="p-6 bg-gray-800/50 border border-gray-700 rounded-xl hover:border-primary-600/50 transition-colors"
              >
                <div className="p-3 bg-primary-600/10 rounded-lg w-fit mb-4">
                  <Icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="font-semibold text-gray-100 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-400">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="py-16">
        <h2 className="text-2xl font-bold text-center text-gray-100 mb-12">Simple 4-Step Process</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {['Enter Topic', 'Edit Script', 'Review Media', 'Get Video'].map((label, i) => (
            <div key={i} className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-600/20 border border-primary-600/30 rounded-full text-primary-400 font-bold text-lg mb-3">
                {i + 1}
              </div>
              <p className="font-medium text-gray-200">{label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
