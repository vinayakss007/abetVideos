import { RefreshCw, Check, X, ArrowRight, Image, Film } from 'lucide-react';
import type { MediaItem } from '../types';

interface MediaPreviewProps {
  mediaItems: MediaItem[];
  onUpdateMedia: (items: MediaItem[]) => void;
  onConfirm: () => void;
  isLoading: boolean;
}

export default function MediaPreview({ mediaItems, onUpdateMedia, onConfirm, isLoading }: MediaPreviewProps) {
  const removeItem = (index: number) => {
    const updated = mediaItems.filter((_, i) => i !== index);
    onUpdateMedia(updated);
  };

  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Film className="w-4 h-4" />;
      default:
        return <Image className="w-4 h-4" />;
    }
  };

  const getSourceBadgeColor = (source: string) => {
    switch (source.toLowerCase()) {
      case 'pexels':
        return 'bg-green-900/50 text-green-300';
      case 'pixabay':
        return 'bg-blue-900/50 text-blue-300';
      case 'giphy':
        return 'bg-purple-900/50 text-purple-300';
      default:
        return 'bg-gray-700 text-gray-300';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">Media Preview</h3>
          <p className="text-sm text-gray-400">
            {mediaItems.length} media items found
          </p>
        </div>
        <button
          type="button"
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
          disabled
        >
          <RefreshCw className="w-4 h-4" />
          Refresh All
        </button>
      </div>

      {mediaItems.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No media items to display</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {mediaItems.map((item, index) => (
            <div
              key={index}
              className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden group"
            >
              <div className="aspect-video bg-gray-900 relative flex items-center justify-center">
                {item.type === 'video' ? (
                  <div className="flex flex-col items-center gap-2 text-gray-500">
                    <Film className="w-8 h-8" />
                    <span className="text-xs">Video</span>
                  </div>
                ) : (
                  <img
                    src={item.url}
                    alt={item.query}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                )}
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => removeItem(index)}
                    className="p-1.5 bg-red-600/80 hover:bg-red-600 rounded-lg text-white"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                  <button
                    type="button"
                    className="p-1.5 bg-green-600/80 hover:bg-green-600 rounded-lg text-white"
                    title="Accept"
                  >
                    <Check className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div className="p-3 space-y-2">
                <div className="flex items-center gap-2">
                  {getMediaIcon(item.type)}
                  <span className="text-xs text-gray-400 truncate">{item.query}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getSourceBadgeColor(item.source)}`}>
                    {item.source}
                  </span>
                  <span className="text-xs text-gray-500 capitalize">{item.type}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={onConfirm}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Processing...' : 'Continue - Generate Video'}
        {!isLoading && <ArrowRight className="w-5 h-5" />}
      </button>
    </div>
  );
}
