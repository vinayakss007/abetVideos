import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Film, Trash2, AlertCircle, RotateCcw } from 'lucide-react';
import { getVideoHistory, getVideoDownloadUrl, getVideoThumbnailUrl } from '../api/client';
import type { HistoryEntry } from '../types';
import apiClient from '../api/client';

function ThumbnailCell({ videoId, title }: { videoId: string; title: string }) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="w-16 h-10 bg-gray-800 rounded-lg overflow-hidden shrink-0 flex items-center justify-center">
      {failed ? (
        <Film className="w-5 h-5 text-primary-400" />
      ) : (
        <img
          src={getVideoThumbnailUrl(videoId)}
          alt={title}
          className="w-full h-full object-cover"
          onError={() => setFailed(true)}
          loading="lazy"
        />
      )}
    </div>
  );
}

export default function History() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getVideoHistory()
      .then((data) => { if (!cancelled) { setHistory(data); setLoading(false); } })
      .catch(() => { if (!cancelled) { setError('Failed to load history'); setLoading(false); } });
    return () => { cancelled = true; };
  }, [refreshKey]);

  async function handleDelete(entryId: string) {
    if (!confirm('Delete this video from history?')) return;
    setDeleting(entryId);
    try {
      await apiClient.delete(`/videos/history/${entryId}`);
      setHistory((prev) => prev.filter((e) => e.id !== entryId));
    } catch {
      setError('Failed to delete entry');
    } finally {
      setDeleting(null);
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 bg-gray-800/50 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" /> Retry
          </button>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <Film className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-300 mb-2">No videos yet</h2>
        <p className="text-gray-500 mb-6">Create your first video to see it here.</p>
        <Link
          to="/create"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-500 text-white rounded-xl transition-colors font-medium"
        >
          Create Video
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Clock className="w-6 h-6 text-primary-400" />
          <h1 className="text-2xl font-bold text-gray-100">History</h1>
          <span className="text-sm text-gray-500">(Last {history.length})</span>
        </div>
        <button
          onClick={async () => {
            if (!confirm('Clear all history?')) return;
            try {
              await apiClient.delete('/videos/history');
              setHistory([]);
            } catch {
              setError('Failed to clear history');
            }
          }}
          className="text-sm px-3 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors"
        >
          Clear All
        </button>
      </div>

      <div className="space-y-3">
        {history.map((entry) => (
          <div
            key={entry.id}
            className="flex items-center gap-4 p-4 bg-gray-900/50 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
          >
            <ThumbnailCell videoId={entry.video_id} title={entry.title} />
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-200 truncate">{entry.title}</h3>
              <p className="text-sm text-gray-500">
                {entry.scenes_count} scenes &middot; {Math.round(entry.duration_seconds)}s &middot; {entry.format}
              </p>
            </div>
            <a
              href={getVideoDownloadUrl(entry.video_id)}
              download={`video-${entry.video_id}.mp4`}
              className="px-4 py-2 bg-primary-600/20 hover:bg-primary-600/40 text-primary-400 rounded-lg transition-colors text-sm font-medium"
            >
              Download
            </a>
            <button
              onClick={() => handleDelete(entry.id)}
              disabled={deleting === entry.id}
              className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
