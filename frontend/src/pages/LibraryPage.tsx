import { useState, useEffect, useCallback } from 'react';
import { Upload, Search, Trash2, Music, Image, Video, FolderOpen } from 'lucide-react';
import toast from 'react-hot-toast';
import type { LibraryItem, LibraryCategory } from '../types';
import * as api from '../api/client';

const CATEGORIES: { value: LibraryCategory; label: string; icon: typeof Music }[] = [
  { value: 'music', label: 'Music', icon: Music },
  { value: 'image', label: 'Image', icon: Image },
  { value: 'video', label: 'Video', icon: Video },
];

const FILTER_TABS: { value: string; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'music', label: 'Music' },
  { value: 'image', label: 'Images' },
  { value: 'video', label: 'Videos' },
];

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [filterCategory, setFilterCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<LibraryCategory>('image');
  const [uploadLabels, setUploadLabels] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  const fetchItems = useCallback(async () => {
    try {
      const data = await api.getLibraryItems(filterCategory || undefined, searchQuery || undefined);
      setItems(data);
    } catch {
      // Error toast handled by API interceptor
    }
  }, [filterCategory, searchQuery]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }
    setUploading(true);
    try {
      await api.uploadLibraryItem(uploadFile, uploadCategory, uploadLabels, uploadDescription);
      toast.success('File uploaded successfully');
      setUploadFile(null);
      setUploadLabels('');
      setUploadDescription('');
      fetchItems();
    } catch {
      // Error toast handled by API interceptor
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteLibraryItem(id);
      toast.success('Item deleted');
      fetchItems();
    } catch {
      // Error toast handled by API interceptor
    }
  };

  const getCategoryIcon = (category: LibraryCategory) => {
    switch (category) {
      case 'music': return <Music className="w-8 h-8 text-purple-400" />;
      case 'image': return <Image className="w-8 h-8 text-green-400" />;
      case 'video': return <Video className="w-8 h-8 text-blue-400" />;
    }
  };

  const getCategoryBadgeColor = (category: LibraryCategory) => {
    switch (category) {
      case 'music': return 'bg-purple-600/20 text-purple-300 border-purple-600/30';
      case 'image': return 'bg-green-600/20 text-green-300 border-green-600/30';
      case 'video': return 'bg-blue-600/20 text-blue-300 border-blue-600/30';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-600 rounded-lg">
          <FolderOpen className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Media Library</h1>
          <p className="text-sm text-gray-400">Upload and manage your stock music, images, and videos</p>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Media
        </h2>
        <form onSubmit={handleUpload} className="space-y-4">
          {/* File Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">File</label>
            <input
              type="file"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-500 file:cursor-pointer"
              accept="audio/*,image/*,video/*"
            />
            {uploadFile && (
              <p className="mt-1 text-xs text-gray-500">{uploadFile.name} ({formatFileSize(uploadFile.size)})</p>
            )}
          </div>

          {/* Category Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
            <div className="grid grid-cols-3 gap-2">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                return (
                  <button
                    key={cat.value}
                    type="button"
                    onClick={() => setUploadCategory(cat.value)}
                    className={`flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                      uploadCategory === cat.value
                        ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {cat.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Labels */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Labels (comma-separated)</label>
            <input
              type="text"
              value={uploadLabels}
              onChange={(e) => setUploadLabels(e.target.value)}
              placeholder="e.g., nature, calm, background"
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              placeholder="Brief description of the media..."
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm resize-none h-20"
            />
          </div>

          <button
            type="submit"
            disabled={uploading || !uploadFile}
            className="flex items-center gap-2 px-6 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </form>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <div className="flex gap-2">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilterCategory(tab.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filterCategory === tab.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by labels or description..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Grid View */}
      {items.length === 0 ? (
        <div className="text-center py-16">
          <FolderOpen className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No items in your library yet. Upload some media to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map((item) => (
            <div key={item.id} className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden hover:border-gray-600 transition-colors">
              {/* Thumbnail / Icon Area */}
              <div className="h-32 bg-gray-900 flex items-center justify-center">
                {item.category === 'image' ? (
                  <img
                    src={`/static/library/images/${item.filename}`}
                    alt={item.original_filename}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                      (e.target as HTMLImageElement).parentElement!.innerHTML = '<div class="flex items-center justify-center h-full"><svg class="w-8 h-8 text-green-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg></div>';
                    }}
                  />
                ) : (
                  getCategoryIcon(item.category)
                )}
              </div>

              {/* Info */}
              <div className="p-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-gray-200 truncate flex-1" title={item.original_filename}>
                    {item.original_filename}
                  </p>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1 text-gray-500 hover:text-red-400 transition-colors shrink-0"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${getCategoryBadgeColor(item.category)}`}>
                    {item.category}
                  </span>
                  <span className="text-xs text-gray-500">{formatFileSize(item.file_size)}</span>
                </div>

                {item.labels.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {item.labels.map((label, idx) => (
                      <span key={idx} className="text-xs px-1.5 py-0.5 bg-gray-700 text-gray-300 rounded">
                        {label}
                      </span>
                    ))}
                  </div>
                )}

                <p className="text-xs text-gray-500">{formatDate(item.created_at)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
