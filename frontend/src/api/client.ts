import axios from 'axios';
import toast from 'react-hot-toast';
import type { VideoRequest, VideoScript, SceneMedia, TTSResult, VideoResult, MediaItem, MediaProviderStatus, SceneMetadata, EditInstruction, PreviewFrame, AIGenerationSettings, LibraryItem, BrandingConfig } from '../types';

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

export async function sourceMedia(script: VideoScript, ai_generation_settings?: AIGenerationSettings): Promise<SceneMedia[]> {
  const response = await apiClient.post<SceneMedia[]>('/videos/source-media', {
    script,
    ai_generation_settings: ai_generation_settings ?? null,
  });
  return response.data;
}

export async function assembleVideo(data: {
  script: VideoScript;
  tts_results: TTSResult[];
  scene_media: SceneMedia[];
  format?: string;
  quality_settings?: import('../types').VideoQualitySettings;
  audio_settings?: import('../types').AudioSettings;
  branding_config?: import('../types').BrandingConfig | null;
}): Promise<VideoResult> {
  const response = await apiClient.post<VideoResult>('/videos/assemble', {
    script: data.script,
    tts_results: data.tts_results,
    scene_media: data.scene_media,
    format: data.format ?? 'landscape',
    quality_settings: data.quality_settings ?? null,
    audio_settings: data.audio_settings ?? null,
    branding_config: data.branding_config ?? null,
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

export async function getProviders(): Promise<MediaProviderStatus[]> {
  const response = await apiClient.get<MediaProviderStatus[]>('/videos/providers');
  return response.data;
}

export async function getScenes(videoId: string): Promise<SceneMetadata[]> {
  const response = await apiClient.get<SceneMetadata[]>(`/videos/${videoId}/scenes`);
  return response.data;
}

export async function submitEdit(videoId: string, instructions: EditInstruction): Promise<{ video_id: string; video_path: string; duration_seconds: number }> {
  const response = await apiClient.post<{ video_id: string; video_path: string; duration_seconds: number }>(`/videos/${videoId}/edit`, { instructions });
  return response.data;
}

export async function getPreviewFrame(videoId: string, timestamp: number): Promise<PreviewFrame> {
  const response = await apiClient.post<PreviewFrame>(`/videos/${videoId}/preview-frame`, { timestamp });
  return response.data;
}

export async function getAISettings(): Promise<AIGenerationSettings> {
  const response = await apiClient.get<AIGenerationSettings>('/videos/ai-settings');
  return response.data;
}

// Library API
export async function uploadLibraryItem(file: File, category: string, labels: string, description: string): Promise<LibraryItem> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('labels', labels);
  formData.append('description', description);
  const response = await apiClient.post<LibraryItem>('/library/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getLibraryItems(category?: string, search?: string): Promise<LibraryItem[]> {
  const params: Record<string, string> = {};
  if (category) params.category = category;
  if (search) params.search = search;
  const response = await apiClient.get<LibraryItem[]>('/library', { params });
  return response.data;
}

export async function deleteLibraryItem(id: string): Promise<void> {
  await apiClient.delete(`/library/${id}`);
}

export async function searchLibrary(query: string): Promise<LibraryItem[]> {
  const response = await apiClient.get<LibraryItem[]>('/library/search', { params: { query } });
  return response.data;
}

// Branding API
export async function uploadBranding(file: File, position: string, sizePercent: number, opacity: number): Promise<BrandingConfig> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('position', position);
  formData.append('size_percent', sizePercent.toString());
  formData.append('opacity', opacity.toString());
  const response = await apiClient.post<BrandingConfig>('/branding/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getBranding(): Promise<BrandingConfig | null> {
  try {
    const response = await apiClient.get<BrandingConfig>('/branding');
    return response.data;
  } catch {
    return null;
  }
}

export async function updateBranding(config: { position?: string; size_percent?: number; opacity?: number; enabled?: boolean }): Promise<BrandingConfig> {
  const response = await apiClient.put<BrandingConfig>('/branding', config);
  return response.data;
}

export async function deleteBranding(): Promise<void> {
  await apiClient.delete('/branding');
}

export default apiClient;
