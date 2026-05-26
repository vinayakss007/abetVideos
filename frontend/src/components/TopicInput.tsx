import { useState } from 'react';
import { Sparkles, Clock, Palette } from 'lucide-react';
import type { VideoRequest, VideoQualitySettings, AudioSettings as AudioSettingsType } from '../types';
import QualitySettings from './QualitySettings';
import AudioSettings from './AudioSettings';

interface TopicInputProps {
  onSubmit: (request: VideoRequest) => void;
  isLoading: boolean;
}

const DEFAULT_QUALITY_SETTINGS: VideoQualitySettings = {
  resolution: '1080p',
  bitrate: 'medium',
  fps: '24',
  codec_preset: 'medium',
  output_format: 'mp4',
};

const DEFAULT_AUDIO_SETTINGS: AudioSettingsType = {
  crossfade_duration: 0.5,
  normalize_audio: true,
  background_music_url: null,
  background_music_volume: 0.15,
  enable_ducking: true,
  generate_subtitles: false,
};

const DURATION_OPTIONS = [
  { value: 0.5, label: '30 seconds' },
  { value: 1, label: '1 minute' },
  { value: 3, label: '3 minutes' },
  { value: 5, label: '5 minutes' },
  { value: 10, label: '10 minutes' },
];

const STYLE_OPTIONS = [
  { value: 'educational', label: 'Educational', icon: '📚' },
  { value: 'entertaining', label: 'Entertaining', icon: '🎬' },
  { value: 'news', label: 'News', icon: '📰' },
  { value: 'documentary', label: 'Documentary', icon: '🎥' },
  { value: 'motivational', label: 'Motivational', icon: '💡' },
];

export default function TopicInput({ onSubmit, isLoading }: TopicInputProps) {
  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState(1);
  const [style, setStyle] = useState('educational');
  const [qualitySettings, setQualitySettings] = useState<VideoQualitySettings>(DEFAULT_QUALITY_SETTINGS);
  const [audioSettings, setAudioSettings] = useState<AudioSettingsType>(DEFAULT_AUDIO_SETTINGS);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit({
      topic: topic.trim(),
      duration_minutes: duration,
      style,
      quality_settings: qualitySettings,
      audio_settings: audioSettings,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div>
        <label htmlFor="topic" className="block text-sm font-medium text-gray-300 mb-2">
          What is your video about?
        </label>
        <textarea
          id="topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter your video topic... e.g., 'The history of space exploration' or 'How to make the perfect coffee'"
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none h-32"
          required
        />
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-3">
          <Clock className="w-4 h-4" />
          Video Duration
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {DURATION_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setDuration(opt.value)}
              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                duration === opt.value
                  ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-3">
          <Palette className="w-4 h-4" />
          Video Style
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {STYLE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setStyle(opt.value)}
              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                style === opt.value
                  ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              <span>{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <QualitySettings settings={qualitySettings} onChange={setQualitySettings} />

      <AudioSettings settings={audioSettings} onChange={setAudioSettings} />

      <button
        type="submit"
        disabled={isLoading || !topic.trim()}
        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg"
      >
        <Sparkles className="w-5 h-5" />
        {isLoading ? 'Generating Script...' : 'Generate Video Script'}
      </button>
    </form>
  );
}
