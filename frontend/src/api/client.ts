import axios from 'axios';
import toast from 'react-hot-toast';
import type { VideoRequest, VideoScript, SceneMedia, TTSResult, VideoResult, MediaItem, MediaProviderStatus, AppSettings, SettingsUpdate, HistoryEntry, AuthResponse, UserResponse, AIModelInfo } from '../types';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/signup') && !window.location.pathname.startsWith('/forgot-password') && !window.location.pathname.startsWith('/reset-password')) {
      window.location.href = '/login';
      return Promise.reject(error);
    }
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

export async function sourceMedia(script: VideoScript, preferred_type?: string): Promise<SceneMedia[]> {
  const response = await apiClient.post<SceneMedia[]>('/videos/source-media', { script, preferred_type });
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

export function getVideoThumbnailUrl(videoId: string): string {
  return `/api/videos/${videoId}/thumbnail`;
}

export function getVideoSubtitlesUrl(videoId: string): string {
  return `/api/videos/${videoId}/subtitles`;
}

export async function searchMedia(query: string): Promise<MediaItem[]> {
  const response = await apiClient.post<MediaItem[]>('/videos/search-media', { query });
  return response.data;
}

export async function getProviders(): Promise<MediaProviderStatus[]> {
  const response = await apiClient.get<MediaProviderStatus[]>('/videos/providers');
  return response.data;
}

export async function getSettings(): Promise<AppSettings> {
  const response = await apiClient.get<AppSettings>('/settings');
  return response.data;
}

export async function updateSettings(data: SettingsUpdate): Promise<AppSettings> {
  const response = await apiClient.put<AppSettings>('/settings', data);
  return response.data;
}

export async function fetchModels(): Promise<AIModelInfo[]> {
  const response = await apiClient.get<AIModelInfo[]>('/settings/models');
  return response.data;
}

export async function getVideoHistory(): Promise<HistoryEntry[]> {
  const response = await apiClient.get<HistoryEntry[]>('/videos/history');
  return response.data;
}

export async function login(data: { email: string; password: string }): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);
  return response.data;
}

export async function signup(data: { email: string; password: string; full_name: string }): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/signup', data);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}

export async function getMe(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>('/auth/me');
  return response.data;
}

export async function updateProfile(data: {
  email?: string;
  full_name?: string;
  current_password?: string;
  new_password?: string;
}): Promise<UserResponse> {
  const response = await apiClient.put<UserResponse>('/auth/profile', data);
  return response.data;
}

export async function downloadWithAuth(url: string, filename: string): Promise<void> {
  const response = await fetch(url, { credentials: 'include' });
  if (!response.ok) throw new Error('Download failed');
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

export async function cancelTask(taskId: string): Promise<void> {
  await apiClient.delete(`/videos/tasks/${taskId}`);
}

export default apiClient;
