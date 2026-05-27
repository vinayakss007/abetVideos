import { useState } from 'react';
import { ChevronDown, ChevronUp, Wand2 } from 'lucide-react';
import type { AIGenerationSettings as AIGenerationSettingsType } from '../types';

interface AIGenerationSettingsProps {
  settings: AIGenerationSettingsType;
  onChange: (settings: AIGenerationSettingsType) => void;
}

const QUALITY_OPTIONS = [
  { value: 'standard', label: 'Standard' },
  { value: 'hd', label: 'HD' },
] as const;

const SIZE_OPTIONS = [
  { value: '1024x1024', label: '1024x1024' },
  { value: '1792x1024', label: '1792x1024 (Landscape)' },
  { value: '1024x1792', label: '1024x1792 (Portrait)' },
] as const;

export default function AIGenerationSettings({ settings, onChange }: AIGenerationSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const update = (partial: Partial<AIGenerationSettingsType>) => {
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
          <Wand2 className="w-4 h-4" />
          AI Generation Settings
        </span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-6 bg-gray-800/50">
          {/* Enable AI Image Fallback */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-300">
              Enable AI Image Fallback
            </label>
            <button
              type="button"
              onClick={() => update({ ai_image_enabled: !settings.ai_image_enabled })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.ai_image_enabled ? 'bg-purple-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.ai_image_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Enable AI Video Fallback */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-300">
              Enable AI Video Fallback
            </label>
            <button
              type="button"
              onClick={() => update({ ai_video_enabled: !settings.ai_video_enabled })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.ai_video_enabled ? 'bg-purple-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.ai_video_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Max AI Images per Video */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max AI Images per Video: {settings.ai_image_max_per_video}
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={settings.ai_image_max_per_video}
              onChange={(e) => update({ ai_image_max_per_video: Number(e.target.value) })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0</span>
              <span>20</span>
            </div>
          </div>

          {/* Max AI Videos per Video */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max AI Videos per Video: {settings.ai_video_max_per_video}
            </label>
            <input
              type="range"
              min={0}
              max={10}
              value={settings.ai_video_max_per_video}
              onChange={(e) => update({ ai_video_max_per_video: Number(e.target.value) })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0</span>
              <span>10</span>
            </div>
          </div>

          {/* AI Image Quality */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">AI Image Quality</label>
            <div className="grid grid-cols-2 gap-2">
              {QUALITY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ ai_image_quality: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.ai_image_quality === opt.value
                      ? 'bg-purple-600 text-white ring-2 ring-purple-400'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* AI Image Size */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">AI Image Size</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {SIZE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => update({ ai_image_size: opt.value })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    settings.ai_image_size === opt.value
                      ? 'bg-purple-600 text-white ring-2 ring-purple-400'
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
