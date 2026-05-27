import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Image, Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import type { BrandingConfig, BrandingPosition } from '../types';
import * as api from '../api/client';

interface BrandingSettingsProps {
  config: BrandingConfig | null;
  onChange: (config: BrandingConfig | null) => void;
}

const POSITIONS: { value: BrandingPosition; label: string }[] = [
  { value: 'top-left', label: 'Top Left' },
  { value: 'top-center', label: 'Top Center' },
  { value: 'top-right', label: 'Top Right' },
  { value: 'bottom-left', label: 'Bottom Left' },
  { value: 'bottom-center', label: 'Bottom Center' },
  { value: 'bottom-right', label: 'Bottom Right' },
];

function getPositionStyle(position: BrandingPosition): React.CSSProperties {
  const base: React.CSSProperties = { position: 'absolute', width: '20%', height: '20%' };
  switch (position) {
    case 'top-left': return { ...base, top: '8%', left: '8%' };
    case 'top-center': return { ...base, top: '8%', left: '40%' };
    case 'top-right': return { ...base, top: '8%', right: '8%' };
    case 'bottom-left': return { ...base, bottom: '8%', left: '8%' };
    case 'bottom-center': return { ...base, bottom: '8%', left: '40%' };
    case 'bottom-right': return { ...base, bottom: '8%', right: '8%' };
  }
}

export default function BrandingSettings({ config, onChange }: BrandingSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [position, setPosition] = useState<BrandingPosition>(config?.position ?? 'bottom-right');
  const [sizePercent, setSizePercent] = useState(config?.size_percent ?? 15);
  const [opacity, setOpacity] = useState(config?.opacity ?? 0.8);
  const [enabled, setEnabled] = useState(config?.enabled ?? true);

  useEffect(() => {
    // Fetch current branding config on mount
    api.getBranding().then((cfg) => {
      if (cfg) {
        onChange(cfg);
        setPosition(cfg.position);
        setSizePercent(cfg.size_percent);
        setOpacity(cfg.opacity);
        setEnabled(cfg.enabled);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const result = await api.uploadBranding(file, position, sizePercent, opacity);
      onChange(result);
      setFile(null);
      toast.success('Branding image uploaded');
    } catch {
      // Error handled by interceptor
    } finally {
      setUploading(false);
    }
  };

  const handleUpdateSettings = async (updates: Partial<{ position: BrandingPosition; size_percent: number; opacity: number; enabled: boolean }>) => {
    const newPosition = updates.position ?? position;
    const newSize = updates.size_percent ?? sizePercent;
    const newOpacity = updates.opacity ?? opacity;
    const newEnabled = updates.enabled ?? enabled;

    setPosition(newPosition);
    setSizePercent(newSize);
    setOpacity(newOpacity);
    setEnabled(newEnabled);

    if (config) {
      try {
        const updated = await api.updateBranding({
          position: newPosition,
          size_percent: newSize,
          opacity: newOpacity,
          enabled: newEnabled,
        });
        onChange(updated);
      } catch {
        // Error handled by interceptor
      }
    } else {
      // No config uploaded yet, just update local state
      onChange(null);
    }
  };

  return (
    <div className="border border-gray-700 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 hover:bg-gray-750 transition-colors"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Image className="w-4 h-4" />
          Branding / Watermark
        </span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-6 bg-gray-800/50">
          {/* Upload branding image */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Branding Image</label>
            {config?.image_path && (
              <div className="mb-2">
                <img
                  src={`/static/branding/${config.image_path.split('/').pop()}`}
                  alt="Current branding"
                  className="h-12 rounded border border-gray-700"
                />
              </div>
            )}
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="flex-1 text-sm text-gray-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-500 file:cursor-pointer"
              />
              <button
                type="button"
                onClick={handleUpload}
                disabled={!file || uploading}
                className="flex items-center gap-1 px-3 py-1.5 bg-primary-600 hover:bg-primary-500 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Upload className="w-3 h-3" />
                {uploading ? '...' : 'Upload'}
              </button>
            </div>
          </div>

          {/* Position Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Position</label>
            <div className="grid grid-cols-3 gap-2">
              {POSITIONS.map((pos) => (
                <button
                  key={pos.value}
                  type="button"
                  onClick={() => handleUpdateSettings({ position: pos.value })}
                  className={`px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    position === pos.value
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </div>

          {/* Size Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Size: {sizePercent}%
            </label>
            <input
              type="range"
              min="10"
              max="50"
              value={sizePercent}
              onChange={(e) => handleUpdateSettings({ size_percent: parseInt(e.target.value) })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10%</span>
              <span>50%</span>
            </div>
          </div>

          {/* Opacity Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Opacity: {opacity.toFixed(1)}
            </label>
            <input
              type="range"
              min="10"
              max="100"
              value={Math.round(opacity * 100)}
              onChange={(e) => handleUpdateSettings({ opacity: parseInt(e.target.value) / 100 })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.1</span>
              <span>1.0</span>
            </div>
          </div>

          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-300">Enable Branding</span>
            <button
              type="button"
              onClick={() => handleUpdateSettings({ enabled: !enabled })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                enabled ? 'bg-primary-600' : 'bg-gray-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Visual Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Preview</label>
            <div className="relative w-full aspect-video bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center text-gray-600 text-xs">
                Video Frame
              </div>
              {enabled && (
                <div
                  style={{ ...getPositionStyle(position), opacity }}
                  className="bg-primary-500 rounded"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
