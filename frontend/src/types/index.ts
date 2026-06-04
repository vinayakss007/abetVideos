export interface VideoQualitySettings {
  resolution: '480p' | '720p' | '1080p' | '4k';
  bitrate: 'low' | 'medium' | 'high' | 'custom';
  custom_bitrate?: string;
  fps: '24' | '30' | '60';
  codec_preset:
    | 'ultrafast'
    | 'superfast'
    | 'veryfast'
    | 'faster'
    | 'fast'
    | 'medium'
    | 'slow'
    | 'slower'
    | 'veryslow';
  output_format: 'mp4' | 'webm' | 'avi';
}

export interface AudioSettings {
  crossfade_duration: number;
  normalize_audio: boolean;
  background_music_url?: string | null;
  background_music_volume: number;
  enable_ducking: boolean;
  generate_subtitles: boolean;
  tts_voice?: string;
}

export const TTS_VOICES = [
  { value: 'en-US-AriaNeural', label: 'English (US) - Aria' },
  { value: 'en-US-JennyNeural', label: 'English (US) - Jenny' },
  { value: 'en-US-GuyNeural', label: 'English (US) - Guy' },
  { value: 'en-GB-SoniaNeural', label: 'English (UK) - Sonia' },
  { value: 'hi-IN-SwaraNeural', label: 'Hindi - Swara' },
  { value: 'hi-IN-MadhurNeural', label: 'Hindi - Madhur' },
];

export interface VideoRequest {
  topic: string;
  duration_minutes: number;
  style: string;
  language?: string;
  quality_settings?: VideoQualitySettings;
  audio_settings?: AudioSettings;
}

const HINDI_VOICES = new Set(['hi-IN-SwaraNeural', 'hi-IN-MadhurNeural']);

export function detectLanguage(voice?: string): string {
  return voice && HINDI_VOICES.has(voice) ? 'hindi' : 'english';
}

export interface ScriptScene {
  scene_number: number;
  narration: string;
  visual_description: string;
  duration_seconds: number;
}

export interface VideoScript {
  title: string;
  scenes: ScriptScene[];
  total_duration: number;
}

export interface MediaItem {
  url: string;
  media_type: 'image' | 'gif' | 'video' | 'sound';
  source: string;
  query: string;
  local_path?: string;
  width?: number | null;
  height?: number | null;
}

export interface SceneMedia {
  scene_number: number;
  media_items: MediaItem[];
}

export interface TTSResult {
  scene_number: number;
  audio_path: string;
  duration_seconds: number;
}

export interface VideoResult {
  video_path: string;
  video_id: string;
  duration_seconds: number;
  scenes_count: number;
  format: string;
  subtitle_path?: string | null;
}

export type GenerationStep =
  | 'idle'
  | 'generating_script'
  | 'editing_script'
  | 'sourcing_media'
  | 'editing_media'
  | 'generating_tts'
  | 'assembling'
  | 'complete'
  | 'error';

export interface MediaProviderStatus {
  name: string;
  configured: boolean;
  media_types: string[];
}

export interface AppSettings {
  openai_api_key: string;
  openai_api_key_configured: boolean;
  openai_base_url: string;
  openai_model: string;
  pexels_api_key: string;
  pexels_api_key_configured: boolean;
  pixabay_api_key: string;
  pixabay_api_key_configured: boolean;
  giphy_api_key: string;
  giphy_api_key_configured: boolean;
  unsplash_access_key: string;
  unsplash_access_key_configured: boolean;
  freesound_api_key: string;
  freesound_api_key_configured: boolean;
  media_cache_enabled: boolean;
  tts_voice: string;
  output_dir: string;
}

export interface SettingsUpdate {
  openai_api_key?: string;
  openai_base_url?: string;
  openai_model?: string;
  pexels_api_key?: string;
  pixabay_api_key?: string;
  giphy_api_key?: string;
  unsplash_access_key?: string;
  freesound_api_key?: string;
  media_cache_enabled?: boolean;
  tts_voice?: string;
  output_dir?: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user_id: string;
  email: string;
  full_name: string;
  token: string;
}

export interface HistoryEntry {
  id: string;
  video_id: string;
  title: string;
  topic: string;
  duration_seconds: number;
  scenes_count: number;
  format: string;
  created_at: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AIModelInfo {
  id: string;
  name: string;
  owned_by: string;
}
