import { useState } from 'react';
import { Search } from 'lucide-react';
import type { MediaItem } from '../../types';
import { searchMedia } from '../../api/client';

interface MediaSwapPanelProps {
  sceneNumber: number;
  currentMediaUrl: string | null;
  onSwap: (newMediaUrl: string, mediaType: string) => void;
}

export default function MediaSwapPanel({ sceneNumber, currentMediaUrl, onSwap }: MediaSwapPanelProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MediaItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const items = await searchMedia(query);
      setResults(items);
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <h4 className="text-sm font-medium text-gray-200">Media Swap - Scene {sceneNumber}</h4>

      {currentMediaUrl && (
        <div className="w-full h-24 bg-gray-900 rounded overflow-hidden border border-gray-700">
          <img
            src={currentMediaUrl}
            alt="Current media"
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search for media..."
          className="flex-1 px-3 py-2 text-sm bg-gray-900 border border-gray-600 rounded text-gray-200 placeholder-gray-500"
        />
        <button
          type="button"
          onClick={handleSearch}
          disabled={isSearching}
          className="px-3 py-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded transition-colors"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>

      {isSearching && (
        <p className="text-xs text-gray-400">Searching...</p>
      )}

      {results.length > 0 && (
        <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
          {results.map((item, index) => (
            <button
              key={index}
              type="button"
              onClick={() => onSwap(item.url, item.media_type)}
              className="aspect-video bg-gray-900 rounded overflow-hidden border border-gray-700 hover:border-primary-500 transition-colors"
            >
              <img
                src={item.url}
                alt={item.query}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {!isSearching && results.length === 0 && query && (
        <p className="text-xs text-gray-500">No results. Try a different search term.</p>
      )}
    </div>
  );
}
