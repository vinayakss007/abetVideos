import { Download, RotateCcw, CheckCircle2 } from 'lucide-react';
import type { VideoResult } from '../types';
import { getVideoDownloadUrl } from '../api/client';

interface VideoPlayerProps {
  result: VideoResult;
  onReset: () => void;
}

export default function VideoPlayer({ result, onReset }: VideoPlayerProps) {
  const downloadUrl = getVideoDownloadUrl(result.video_id);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600/20 rounded-full mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-400" />
        </div>
        <h3 className="text-xl font-semibold text-gray-100">Video Generated!</h3>
        <p className="text-sm text-gray-400 mt-1">
          {result.scenes_count} scenes - {Math.round(result.duration_seconds)}s duration
        </p>
      </div>

      <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
        <video
          src={downloadUrl}
          controls
          className="w-full aspect-video bg-black"
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <a
          href={downloadUrl}
          download
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all"
        >
          <Download className="w-5 h-5" />
          Download Video
        </a>
        <button
          type="button"
          onClick={onReset}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 font-semibold rounded-xl transition-colors"
        >
          <RotateCcw className="w-5 h-5" />
          Create Another
        </button>
      </div>
    </div>
  );
}
