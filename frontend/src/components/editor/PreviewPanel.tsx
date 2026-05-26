import { useState } from 'react';
import { Eye } from 'lucide-react';
import type { SceneMetadata, PreviewFrame } from '../../types';
import { getPreviewFrame } from '../../api/client';

interface PreviewPanelProps {
  videoId: string;
  sceneNumber: number;
  scene: SceneMetadata;
  sceneStartOffset: number;
}

export default function PreviewPanel({ videoId, sceneNumber, scene, sceneStartOffset }: PreviewPanelProps) {
  const [timestamp, setTimestamp] = useState(0);
  const [frame, setFrame] = useState<PreviewFrame | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadFrame = async () => {
    setIsLoading(true);
    try {
      const absoluteTimestamp = sceneStartOffset + timestamp;
      const result = await getPreviewFrame(videoId, absoluteTimestamp);
      setFrame(result);
    } catch {
      setFrame(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <h4 className="text-sm font-medium text-gray-200">Preview - Scene {sceneNumber}</h4>

      <div className="w-full aspect-video bg-gray-900 rounded overflow-hidden border border-gray-700">
        {frame ? (
          <img
            src={`data:image/jpeg;base64,${frame.frame_data}`}
            alt={`Frame at ${frame.timestamp}s`}
            className="w-full h-full object-contain"
          />
        ) : scene.thumbnail_url ? (
          <img
            src={scene.thumbnail_url}
            alt={`Scene ${sceneNumber} thumbnail`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-gray-500 text-sm">No preview available</span>
          </div>
        )}
      </div>

      {frame && (
        <p className="text-xs text-gray-500">
          {frame.width}x{frame.height} at {frame.timestamp.toFixed(1)}s
        </p>
      )}

      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Timestamp: {timestamp.toFixed(1)}s
        </label>
        <input
          type="range"
          min={0}
          max={scene.duration_seconds}
          step={0.1}
          value={timestamp}
          onChange={(e) => setTimestamp(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
        />
      </div>

      <button
        type="button"
        onClick={handleLoadFrame}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded transition-colors"
      >
        <Eye className="w-4 h-4" />
        {isLoading ? 'Loading...' : 'Load Frame'}
      </button>
    </div>
  );
}
