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

export interface VideoRequest {
  topic: string;
  duration_minutes: number;
  style: string;
  quality_settings?: VideoQualitySettings;
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
  media_type: 'image' | 'gif' | 'video';
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
