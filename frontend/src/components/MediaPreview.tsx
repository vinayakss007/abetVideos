import { useState } from 'react';
import { RefreshCw, Check, X, ArrowRight, Image, Film, Search, Music, Volume2 } from 'lucide-react';
import type { MediaItem, SceneMedia } from '../types';
import { searchMedia } from '../api/client';

interface MediaPreviewProps {
  sceneMedia: SceneMedia[];
  onUpdateMedia: (items: SceneMedia[]) => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function getResolutionBadge(width?: number | null, height?: number | null): string | null {
  if (!width || !height) return null;
  if (width >= 3840 || height >= 2160) return '4K';
  if (width >= 1920 || height >= 1080) return 'HD';
  return null;
}

export default function MediaPreview({ sceneMedia, onUpdateMedia, onConfirm, isLoading }: MediaPreviewProps) {
  const [searchingScene, setSearchingScene] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MediaItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Flatten all media items for display
  const allItems: { item: MediaItem; sceneIndex: number; itemIndex: number }[] = [];
  sceneMedia.forEach((scene, sceneIndex) => {
    scene.media_items.forEach((item, itemIndex) => {
      allItems.push({ item, sceneIndex, itemIndex });
    });
  });

  const removeItem = (sceneIdx: number, itemIdx: number) => {
    const updated = sceneMedia.map((scene, si) => {
      if (si !== sceneIdx) return scene;
      return {
        ...scene,
        media_items: scene.media_items.filter((_, ii) => ii !== itemIdx),
      };
    });
    onUpdateMedia(updated);
  };

  const handleSearchMore = (sceneIndex: number) => {
    setSearchingScene(sceneIndex);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await searchMedia(searchQuery.trim());
      setSearchResults(results);
    } catch {
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectResult = (item: MediaItem) => {
    if (searchingScene === null) return;
    const updated = sceneMedia.map((scene, si) => {
      if (si !== searchingScene) return scene;
      return {
        ...scene,
        media_items: [item, ...scene.media_items.slice(0, 2)],
      };
    });
    onUpdateMedia(updated);
    setSearchingScene(null);
    setSearchResults([]);
    setSearchQuery('');
  };

  const getMediaIcon = (mediaType: string) => {
    switch (mediaType) {
      case 'video':
        return <Film className="w-4 h-4" />;
      case 'sound':
        return <Volume2 className="w-4 h-4" />;
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
      case 'unsplash':
        return 'bg-orange-900/50 text-orange-300';
      case 'freesound':
        return 'bg-teal-900/50 text-teal-300';
      case 'generated':
        return 'bg-yellow-900/50 text-yellow-300';
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
            {allItems.length} media items found across {sceneMedia.length} scenes
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

      {allItems.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No media items to display</p>
        </div>
      ) : (
        <div className="space-y-6">
          {sceneMedia.map((scene, sceneIndex) => (
            <div key={scene.scene_number} className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-300">
                  Scene {scene.scene_number}
                </h4>
                <button
                  type="button"
                  onClick={() => handleSearchMore(sceneIndex)}
                  className="flex items-center gap-1 px-2 py-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs text-gray-300 transition-colors"
                >
                  <Search className="w-3 h-3" />
                  Search More
                </button>
              </div>

              {searchingScene === sceneIndex && (
                <div className="p-3 bg-gray-800/80 border border-gray-700 rounded-xl space-y-3">
                  <form onSubmit={handleSearchSubmit} className="flex gap-2">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search for media..."
                      className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500"
                    />
                    <button
                      type="submit"
                      disabled={isSearching || !searchQuery.trim()}
                      className="px-3 py-2 bg-primary-600 hover:bg-primary-500 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSearching ? 'Searching...' : 'Search'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSearchingScene(null);
                        setSearchResults([]);
                        setSearchQuery('');
                      }}
                      className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg"
                    >
                      Cancel
                    </button>
                  </form>

                  {searchResults.length > 0 && (
                    <div className="grid grid-cols-3 gap-2">
                      {searchResults.map((result, idx) => {
                        const badge = getResolutionBadge(result.width, result.height);
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSelectResult(result)}
                            className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden border border-gray-700 hover:border-primary-500 transition-colors group"
                          >
                            {result.media_type === 'image' || result.media_type === 'gif' ? (
                              <img
                                src={result.url}
                                alt={result.query}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            ) : result.media_type === 'sound' ? (
                              <div className="flex flex-col items-center justify-center h-full gap-1 text-gray-500">
                                <Music className="w-6 h-6" />
                                <span className="text-xs">Sound</span>
                              </div>
                            ) : (
                              <div className="flex flex-col items-center justify-center h-full gap-1 text-gray-500">
                                <Film className="w-6 h-6" />
                                <span className="text-xs">Video</span>
                              </div>
                            )}
                            <div className="absolute bottom-1 left-1 flex gap-1">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${getSourceBadgeColor(result.source)}`}>
                                {result.source}
                              </span>
                              {badge && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary-900/50 text-primary-300">
                                  {badge}
                                </span>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {scene.media_items.map((item, itemIndex) => {
                  const badge = getResolutionBadge(item.width, item.height);
                  return (
                    <div
                      key={itemIndex}
                      className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden group"
                    >
                      <div className="aspect-video bg-gray-900 relative flex items-center justify-center">
                        {item.media_type === 'video' ? (
                          <div className="flex flex-col items-center gap-2 text-gray-500">
                            <Film className="w-8 h-8" />
                            <span className="text-xs">Video</span>
                          </div>
                        ) : item.media_type === 'sound' ? (
                          <div className="flex flex-col items-center gap-2 text-gray-500">
                            <Volume2 className="w-8 h-8" />
                            <span className="text-xs">Sound</span>
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
                        {badge && (
                          <span className="absolute top-2 left-2 text-[10px] px-1.5 py-0.5 rounded bg-primary-900/70 text-primary-200 font-medium">
                            {badge}
                          </span>
                        )}
                        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            type="button"
                            onClick={() => removeItem(sceneIndex, itemIndex)}
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
                          {getMediaIcon(item.media_type)}
                          <span className="text-xs text-gray-400 truncate">{item.query}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getSourceBadgeColor(item.source)}`}>
                            {item.source}
                          </span>
                          <span className="text-xs text-gray-500 capitalize">{item.media_type}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
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
