import axios from 'axios';
import toast from 'react-hot-toast';
import type { VideoRequest, VideoScript, SceneMedia, TTSResult, VideoResult, MediaItem } from '../types';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
    toast.error(message);
    return Promise.reject(error);
  }
);

export async function generateScript(request: VideoRequest): Promise<VideoScript> {
  const response = await apiClient.post<VideoScript>('/videos/generate-script', request);
  return response.data;
}

export async function generateTTS(script: VideoScript, voice?: string): Promise<TTSResult[]> {
  const response = await apiClient.post<TTSResult[]>('/videos/generate-tts', {
    script,
    voice: voice ?? null,
  });
  return response.data;
}

export async function sourceMedia(script: VideoScript): Promise<SceneMedia[]> {
  const response = await apiClient.post<SceneMedia[]>('/videos/source-media', { script });
  return response.data;
}

export async function assembleVideo(data: {
  script: VideoScript;
  tts_results: TTSResult[];
  scene_media: SceneMedia[];
  format?: string;
  quality_settings?: import('../types').VideoQualitySettings;
  audio_settings?: import('../types').AudioSettings;
}): Promise<VideoResult> {
  const response = await apiClient.post<VideoResult>('/videos/assemble', {
    script: data.script,
    tts_results: data.tts_results,
    scene_media: data.scene_media,
    format: data.format ?? 'landscape',
    quality_settings: data.quality_settings ?? null,
    audio_settings: data.audio_settings ?? null,
  });
  return response.data;
}

export function getVideoDownloadUrl(videoId: string): string {
  return `/api/videos/${videoId}/download`;
}

export function getVideoSubtitlesUrl(videoId: string): string {
  return `/api/videos/${videoId}/subtitles`;
}

export async function searchMedia(query: string): Promise<MediaItem[]> {
  const response = await apiClient.post<MediaItem[]>('/videos/search-media', { query });
  return response.data;
}

export default apiClient;
