import { useState } from 'react';
import { ChevronDown, ChevronUp, Volume2 } from 'lucide-react';
import type { AudioSettings as AudioSettingsType } from '../types';

interface AudioSettingsProps {
  settings: AudioSettingsType;
  onChange: (settings: AudioSettingsType) => void;
}

export default function AudioSettings({ settings, onChange }: AudioSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const update = (partial: Partial<AudioSettingsType>) => {
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
          <Volume2 className="w-4 h-4" />
          Audio Settings
        </span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-6 bg-gray-800/50">
          {/* Normalize Audio Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-300">
              Normalize Audio
            </label>
            <button
              type="button"
              onClick={() => update({ normalize_audio: !settings.normalize_audio })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.normalize_audio ? 'bg-primary-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.normalize_audio ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Crossfade Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Crossfade Duration: {settings.crossfade_duration.toFixed(1)}s
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.crossfade_duration}
              onChange={(e) => update({ crossfade_duration: parseFloat(e.target.value) })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0s</span>
              <span>2s</span>
            </div>
          </div>

          {/* Generate Subtitles Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-300">
              Generate Subtitles
            </label>
            <button
              type="button"
              onClick={() => update({ generate_subtitles: !settings.generate_subtitles })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.generate_subtitles ? 'bg-primary-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.generate_subtitles ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Background Music URL */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Background Music URL (optional)
            </label>
            <input
              type="url"
              value={settings.background_music_url || ''}
              onChange={(e) => update({ background_music_url: e.target.value || null })}
              placeholder="https://example.com/music.mp3"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Background Music Volume */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Music Volume: {Math.round(settings.background_music_volume * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={Math.round(settings.background_music_volume * 100)}
              onChange={(e) => update({ background_music_volume: parseInt(e.target.value) / 100 })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Auto-Ducking Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-300">
              Auto-Duck During Narration
            </label>
            <button
              type="button"
              onClick={() => update({ enable_ducking: !settings.enable_ducking })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.enable_ducking ? 'bg-primary-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.enable_ducking ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
