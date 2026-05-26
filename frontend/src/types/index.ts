export interface VideoRequest {
  topic: string;
  duration_minutes: number;
  style: string;
}

export interface ScriptScene {
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
  type: 'image' | 'gif' | 'video';
  source: string;
  query: string;
  local_path?: string;
}

export interface TTSResult {
  audio_path: string;
  duration: number;
}

export interface VideoResult {
  video_path: string;
  video_id: string;
  duration: number;
  scenes_count: number;
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
