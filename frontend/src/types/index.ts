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
}

export interface AIGenerationSettings {
  ai_image_enabled: boolean;
  ai_video_enabled: boolean;
  ai_image_max_per_video: number;
  ai_video_max_per_video: number;
  ai_image_quality: 'standard' | 'hd';
  ai_image_size: '1024x1024' | '1792x1024' | '1024x1792';
}

export interface AIGenerationStats {
  ai_images_generated: number;
  ai_videos_generated: number;
  ai_image_limit: number;
  ai_video_limit: number;
}

export type LibraryCategory = 'music' | 'image' | 'video';

export interface LibraryItem {
  id: string;
  filename: string;
  original_filename: string;
  category: LibraryCategory;
  labels: string[];
  description: string;
  file_path: string;
  created_at: string;
  file_size: number;
}

export type BrandingPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'top-center' | 'bottom-center';

export interface BrandingConfig {
  id: string;
  image_path: string;
  position: BrandingPosition;
  size_percent: number;
  opacity: number;
  enabled: boolean;
}

export interface VideoRequest {
  topic: string;
  duration_minutes: number;
  style: string;
  quality_settings?: VideoQualitySettings;
  audio_settings?: AudioSettings;
  ai_generation_settings?: AIGenerationSettings;
  branding_config?: BrandingConfig | null;
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

// Editor types

export interface TextOverlayInstruction {
  text: string;
  x: number; // 0-100 percentage
  y: number; // 0-100 percentage
  font_size: number;
  color: string;
  scene_number: number;
}

export interface SceneTrim {
  scene_number: number;
  start_time: number;
  end_time: number;
}

export interface SceneAudioLevel {
  scene_number: number;
  volume: number; // 0.0 to 2.0
}

export interface MediaReplacement {
  scene_number: number;
  media_url: string;
  media_type: string;
}

export interface EditInstruction {
  scene_order: number[];
  trims: SceneTrim[];
  text_overlays: TextOverlayInstruction[];
  audio_levels: SceneAudioLevel[];
  background_music_volume: number;
  media_replacements: MediaReplacement[];
}

export interface SceneMetadata {
  scene_number: number;
  thumbnail_url: string;
  duration_seconds: number;
  narration: string;
  visual_description: string;
  media_url: string | null;
}

export interface PreviewFrame {
  frame_data: string; // base64 JPEG
  timestamp: number;
  width: number;
  height: number;
}
