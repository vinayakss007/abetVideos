import { useState } from 'react';
import { Music, Play, Check, Loader2 } from 'lucide-react';
import axios from 'axios';

const MOODS = ['calm', 'happy', 'energetic', 'dramatic', 'inspirational', 'professional', 'mysterious'];

interface MusicTrack {
  id: string;
  title: string;
  mood: string;
  duration: number;
  url: string;
  source: string;
}

interface MusicBrowserProps {
  onSelect: (url: string) => void;
  currentUrl?: string | null;
}

export default function MusicBrowser({ onSelect, currentUrl }: MusicBrowserProps) {
  const [mood, setMood] = useState('calm');
  const [tracks, setTracks] = useState<MusicTrack[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewId, setPreviewId] = useState<string | null>(null);

  const search = async (m: string) => {
    setMood(m);
    setLoading(true);
    try {
      const token = localStorage.getItem('abet_token');
      const res = await axios.get<MusicTrack[]>(`/api/videos/music-search?query=${m}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setTracks(res.data);
    } catch {
      setTracks([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Music className="w-4 h-4 text-primary-400" />
        <span className="text-sm font-medium text-gray-300">Background Music</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {MOODS.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => search(m)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              mood === m
                ? 'bg-primary-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200 border border-gray-700'
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {currentUrl && (
        <div className="flex items-center gap-2 p-2 bg-green-900/20 border border-green-700/30 rounded-lg">
          <Check className="w-3 h-3 text-green-400" />
          <span className="text-xs text-green-300">Music selected</span>
          <button
            type="button"
            onClick={() => onSelect('')}
            className="ml-auto text-xs text-gray-500 hover:text-red-400"
          >
            Remove
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        </div>
      )}

      {!loading && tracks.length > 0 && (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {tracks.map((track) => (
            <div
              key={track.id}
              className="flex items-center gap-3 p-2 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <button
                type="button"
                onClick={() => setPreviewId(previewId === track.id ? null : track.id)}
                className="p-1.5 bg-gray-700 rounded-full hover:bg-gray-600 transition-colors"
              >
                <Play className="w-3 h-3 text-gray-300" />
              </button>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">{track.title}</p>
                <p className="text-xs text-gray-500">{track.source} &middot; {track.duration}s</p>
              </div>
              <button
                type="button"
                onClick={() => onSelect(track.url)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  currentUrl === track.url
                    ? 'bg-primary-600 text-white'
                    : 'bg-primary-600/20 text-primary-400 hover:bg-primary-600/40'
                }`}
              >
                {currentUrl === track.url ? 'Selected' : 'Use'}
              </button>
            </div>
          ))}
        </div>
      )}

      {previewId && (
        <audio
          key={previewId}
          src={tracks.find((t) => t.id === previewId)?.url}
          controls
          className="w-full h-8"
          autoPlay
        />
      )}
    </div>
  );
}
