import { useEffect, useState } from 'react';
import {
  Settings,
  Globe,
  Cpu,
  Image,
  Film,
  Music,
  GripVertical,
  Save,
  RefreshCw,
  ExternalLink,
  ToggleLeft,
  Search,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getSettings, updateSettings, fetchModels } from '../api/client';
import type { AppSettings, SettingsUpdate, AIModelInfo } from '../types';

type EditMode = Record<string, boolean>;

const PROVIDERS = [
  { key: 'pexels_api_key' as const, label: 'Pexels', icon: Film, url: 'https://www.pexels.com/api/' },
  { key: 'pixabay_api_key' as const, label: 'Pixabay', icon: Image, url: 'https://pixabay.com/api/docs/' },
  { key: 'giphy_api_key' as const, label: 'Giphy', icon: GripVertical, url: 'https://developers.giphy.com/' },
  { key: 'unsplash_access_key' as const, label: 'Unsplash', icon: Image, url: 'https://unsplash.com/developers' },
  { key: 'freesound_api_key' as const, label: 'Freesound', icon: Music, url: 'https://freesound.org/docs/api/' },
] as const;

const TTS_VOICES = [
  'en-US-AriaNeural',
  'en-US-JennyNeural',
  'en-US-GuyNeural',
  'en-GB-SoniaNeural',
  'en-GB-RyanNeural',
  'en-AU-NatashaNeural',
  'en-AU-WilliamNeural',
  'en-IN-NeerjaNeural',
  'en-IN-PrabhatNeural',
];

const LLM_PRESETS = [
  { name: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { name: 'OpenRouter', baseUrl: 'https://api.openrouter.ai/v1', model: 'gpt-4o-mini' },
  { name: 'Groq', baseUrl: 'https://api.groq.com/openai/v1', model: 'llama-3.3-70b-versatile' },
  { name: 'DeepSeek', baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: 'Together', baseUrl: 'https://api.together.xyz/v1', model: 'mistralai/Mixtral-8x7B-Instruct-v0.1' },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState<EditMode>({});
  const [form, setForm] = useState<SettingsUpdate>({});
  const [availableModels, setAvailableModels] = useState<AIModelInfo[]>([]);
  const [scanningModels, setScanningModels] = useState(false);
  const [modelScanError, setModelScanError] = useState<string | null>(null);

  useEffect(() => {
    getSettings()
      .then((data) => {
        setSettings(data);
        setForm({});
      })
      .catch(() => toast.error('Failed to load settings'))
      .finally(() => setLoading(false));
  }, []);

  function toggleEdit(key: string) {
    setEditMode((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function setValue(key: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleScanModels() {
    setScanningModels(true);
    setModelScanError(null);
    try {
      const models = await fetchModels();
      setAvailableModels(models);
      if (models.length === 0) {
        setModelScanError('No models returned. Check your base URL and API key.');
      } else {
        toast.success(`Found ${models.length} models`);
      }
    } catch {
      setModelScanError('Failed to fetch models. Check your base URL and API key.');
      setAvailableModels([]);
    } finally {
      setScanningModels(false);
    }
  }

  function applyPreset(preset: typeof LLM_PRESETS[number]) {
    setForm((prev) => ({
      ...prev,
      openai_base_url: preset.baseUrl,
      openai_model: preset.model,
    }));
    setAvailableModels([]);
    setModelScanError(null);
  }

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateSettings(form);
      setSettings(updated);
      setForm({});
      setEditMode({});
      toast.success('Settings saved');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  }

  function hasChanges() {
    return Object.keys(form).length > 0;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <RefreshCw className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-600/20 rounded-lg">
            <Settings className="w-6 h-6 text-primary-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        </div>
        <button
          onClick={handleSave}
          disabled={!hasChanges() || saving}
          className="flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors font-medium text-sm"
        >
          {saving ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Changes
        </button>
      </div>

      <div className="space-y-6">
        {/* OpenAI Section */}
        <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Cpu className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-100">AI Provider (OpenAI-compatible)</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">API Key</label>
              <div className="flex gap-2">
                {editMode.openai_api_key ? (
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={form.openai_api_key ?? ''}
                    onChange={(e) => setValue('openai_api_key', e.target.value)}
                    className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
                  />
                ) : (
                  <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-400">
                    {settings?.openai_api_key_configured ? (
                      <><span className="text-green-400">●</span> Configured</>
                    ) : (
                      <><span className="text-red-400">●</span> Not configured</>
                    )}
                  </div>
                )}
                <button
                  onClick={() => toggleEdit('openai_api_key')}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors"
                >
                  {editMode.openai_api_key ? 'Cancel' : 'Change'}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Base URL</label>
              <input
                type="text"
                value={form.openai_base_url ?? settings?.openai_base_url ?? ''}
                onChange={(e) => setValue('openai_base_url', e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Model
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    list="model-suggestions"
                    type="text"
                    value={form.openai_model ?? settings?.openai_model ?? ''}
                    onChange={(e) => setValue('openai_model', e.target.value)}
                    placeholder="Type or select a model"
                    className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
                  />
                  <datalist id="model-suggestions">
                    {availableModels.map((m) => (
                      <option key={m.id} value={m.id} />
                    ))}
                  </datalist>
                </div>
                <button
                  type="button"
                  onClick={handleScanModels}
                  disabled={scanningModels}
                  className="flex items-center gap-1.5 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 text-gray-300 rounded-lg text-sm transition-colors shrink-0"
                >
                  {scanningModels ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  Scan
                </button>
              </div>
              {modelScanError && (
                <p className="flex items-center gap-1 mt-1.5 text-xs text-red-400">
                  <AlertCircle className="w-3 h-3" />
                  {modelScanError}
                </p>
              )}
              {availableModels.length > 0 && !modelScanError && (
                <p className="flex items-center gap-1 mt-1.5 text-xs text-green-400">
                  <CheckCircle2 className="w-3 h-3" />
                  {availableModels.length} models available — type to filter or pick from suggestions
                </p>
              )}
            </div>
          </div>

          {/* Provider presets */}
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500 mb-2">Quick-fill presets:</p>
            <div className="flex flex-wrap gap-2">
              {LLM_PRESETS.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs transition-colors"
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Media Providers Section */}
        <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Globe className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-100">Media Providers</h2>
          </div>
          <div className="space-y-4">
            {PROVIDERS.map(({ key, label, icon: Icon, url }) => (
              <div key={key} className="flex items-center gap-4 p-3 bg-gray-900/50 rounded-lg">
                <Icon className="w-5 h-5 text-gray-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-200 text-sm">{label}</span>
                    {settings?.[`${key}_configured` as keyof AppSettings] ? (
                      <span className="text-xs text-green-400">Connected</span>
                    ) : (
                      <span className="text-xs text-gray-500">Not configured</span>
                    )}
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-auto text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1"
                    >
                      Get API Key <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="flex gap-2">
                    {editMode[key] ? (
                      <input
                        type="password"
                        placeholder={`Enter ${label} API key`}
                        value={(form as Record<string, string | undefined>)[key] ?? ''}
                        onChange={(e) => setValue(key, e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-gray-800 border border-gray-600 rounded text-gray-100 text-sm focus:outline-none focus:border-primary-500"
                      />
                    ) : (
                      <span className="text-sm text-gray-500">
                        {settings?.[`${key}_configured` as keyof AppSettings]
                          ? 'Configured'
                          : 'No key set'}
                      </span>
                    )}
                    <button
                      onClick={() => toggleEdit(key)}
                      className="text-xs px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors shrink-0"
                    >
                      {editMode[key] ? 'Cancel' : 'Change'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* TTS Section */}
        <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Music className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-100">Text-to-Speech</h2>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Voice</label>
            <select
              defaultValue={settings?.tts_voice}
              onChange={(e) => setValue('tts_voice', e.target.value)}
              className="w-full max-w-xs px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
            >
              {TTS_VOICES.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
        </section>

        {/* General Section */}
        <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <ToggleLeft className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-100">General</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-200">Media Cache</span>
                <p className="text-xs text-gray-500">Cache downloaded media files to avoid re-downloading</p>
              </div>
              <button
                onClick={() => setValue('media_cache_enabled', !(form.media_cache_enabled ?? settings?.media_cache_enabled))}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  (form.media_cache_enabled ?? settings?.media_cache_enabled) ? 'bg-primary-600' : 'bg-gray-600'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                    (form.media_cache_enabled ?? settings?.media_cache_enabled) ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Output Directory</label>
              <input
                type="text"
                defaultValue={settings?.output_dir}
                onChange={(e) => setValue('output_dir', e.target.value)}
                className="w-full max-w-sm px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>
        </section>

        {/* Personal Storage Section */}
        <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Film className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-100">Personal Media Storage</h2>
          </div>
          <p className="text-sm text-gray-400 mb-4">
            Upload your own GIFs, images, and short videos to use as media sources for video generation.
            Media files are stored locally and can be selected during the video creation process.
          </p>
          <div className="p-6 bg-gray-900/30 border-2 border-dashed border-gray-600 rounded-lg text-center">
            <Film className="w-10 h-10 text-gray-500 mx-auto mb-3" />
            <p className="text-sm text-gray-400 mb-1">Upload your media files here</p>
            <p className="text-xs text-gray-500">Supported: GIF, MP4, WebM, PNG, JPG, WebP</p>
            <button className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors cursor-not-allowed opacity-60">
              Upload (Coming Soon)
            </button>
          </div>
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">Where GIFs & Short Videos Come From</h3>
            <ul className="text-sm text-gray-400 space-y-1.5">
              <li><span className="text-primary-400">Giphy</span> — Animated GIFs for scene visuals</li>
              <li><span className="text-primary-400">Pexels</span> — Stock videos and images</li>
              <li><span className="text-primary-400">Pixabay</span> — Stock videos and images</li>
              <li><span className="text-primary-400">Unsplash</span> — High-resolution photos</li>
              <li><span className="text-primary-400">Freesound</span> — Sound effects and audio clips</li>
            </ul>
            <p className="text-xs text-gray-500 mt-2">
              Configure API keys above to enable these sources. Without keys, the app falls back
              to text-on-background images.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
