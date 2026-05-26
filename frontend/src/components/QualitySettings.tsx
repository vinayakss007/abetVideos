import { useState } from 'react';
import { ChevronDown, ChevronUp, Settings } from 'lucide-react';
import type { VideoQualitySettings } from '../types';

interface QualitySettingsProps {
  settings: VideoQualitySettings;
  onChange: (settings: VideoQualitySettings) => void;
}

const RESOLUTION_OPTIONS = [
  { value: '480p', label: '480p' },
  { value: '720p', label: '720p' },
  { value: '1080p', label: '1080p' },
  { value: '4k', label: '4K' },
] as const;

const BITRATE_OPTIONS = [
  { value: 'low', label: 'Low (1 Mbps)' },
  { value: 'medium', label: 'Medium (4 Mbps)' },
  { value: 'high', label: 'High (8 Mbps)' },
  { value: 'custom', label: 'Custom' },
] as const;

const FPS_OPTIONS = [
  { value: '24', label: '24 fps' },
  { value: '30', label: '30 fps' },
  { value: '60', label: '60 fps' },
] as const;

const CODEC_PRESET_OPTIONS = [
  { value: 'ultrafast', label: 'Ultrafast' },
  { value: 'superfast', label: 'Superfast' },
  { value: 'veryfast', label: 'Very Fast' },
  { value: 'faster', label: 'Faster' },
  { value: 'fast', label: 'Fast' },
  { value: 'medium', label: 'Medium' },
  { value: 'slow', label: 'Slow' },
  { value: 'slower', label: 'Slower' },
  { value: 'veryslow', label: 'Very Slow' },
] as const;

const OUTPUT_FORMAT_OPTIONS = [
  { value: 'mp4', label: 'MP4' },
  { value: 'webm', label: 'WebM' },
  { value: 'avi', label: 'AVI' },
] as const;

export default function QualitySettings({ settings, onChange }: QualitySettingsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const update = (partial: Partial<VideoQualitySettings>) => {
    onChange({ ...settings, ...partial });
  };

  return (
    <div className="border border-gray-700 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 hover:bg-gray-750 transition-colors"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Settings className="w-4 h-4" />
          Advanced Quality Settings
        </span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-6 bg-gray-800/50">
          {/* Resolution */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Resolution</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {RESOLUTION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ resolution: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.resolution === opt.value
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Bitrate */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Bitrate</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {BITRATE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ bitrate: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.bitrate === opt.value
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {settings.bitrate === 'custom' && (
              <input
                type="text"
                value={settings.custom_bitrate || ''}
                onChange={(e) => update({ custom_bitrate: e.target.value })}
                placeholder="e.g. 6M"
                className="mt-2 w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              />
            )}
          </div>

          {/* FPS */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Frame Rate</label>
            <div className="grid grid-cols-3 gap-2">
              {FPS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ fps: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.fps === opt.value
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Codec Preset */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Encoding Speed</label>
            <select
              value={settings.codec_preset}
              onChange={(e) => update({ codec_preset: e.target.value as VideoQualitySettings['codec_preset'] })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              {CODEC_PRESET_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Output Format */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Output Format</label>
            <div className="grid grid-cols-3 gap-2">
              {OUTPUT_FORMAT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ output_format: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.output_format === opt.value
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
