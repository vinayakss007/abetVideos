import { useState } from 'react';
import { Headphones, Loader2 } from 'lucide-react';
import type { VideoScript, TTSResult } from '../types';
import * as api from '../api/client';

interface VoicePreviewProps {
  script: VideoScript;
  voice?: string;
  onGenerated?: (results: TTSResult[]) => void;
}

export default function VoicePreview({ script, voice, onGenerated }: VoicePreviewProps) {
  const [ttsResults, setTtsResults] = useState<TTSResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleGenerateVoice = async () => {
    setLoading(true);
    try {
      const results = await api.generateTTS(script, voice);
      setTtsResults(results);
      onGenerated?.(results);
    } catch {
      // error handled by api client toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {ttsResults.length === 0 ? (
        <button
          type="button"
          onClick={handleGenerateVoice}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl text-gray-300 font-medium transition-colors disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Headphones className="w-4 h-4" />
          )}
          {loading ? 'Generating Voice...' : 'Generate Voice Preview'}
        </button>
      ) : (
        <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Headphones className="w-4 h-4 text-primary-400" />
              <span className="text-sm font-medium text-gray-200">Voice Generated</span>
            </div>
            <button
              type="button"
              onClick={handleGenerateVoice}
              disabled={loading}
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >
              Regenerate
            </button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {ttsResults.map((r) => (
              <div
                key={r.scene_number}
                className="flex items-center justify-between p-2 bg-gray-800 rounded-lg"
              >
                <span className="text-sm text-gray-400">
                  Scene {r.scene_number} ({Math.round(r.duration_seconds)}s)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
