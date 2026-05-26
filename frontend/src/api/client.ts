import axios from 'axios';
import toast from 'react-hot-toast';
import type { VideoRequest, VideoScript, MediaItem, TTSResult, VideoResult } from '../types';

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

export async function generateTTS(script: VideoScript): Promise<TTSResult[]> {
  const response = await apiClient.post<TTSResult[]>('/videos/generate-tts', script);
  return response.data;
}

export async function sourceMedia(script: VideoScript): Promise<MediaItem[]> {
  const response = await apiClient.post<MediaItem[]>('/videos/source-media', script);
  return response.data;
}

export async function assembleVideo(data: {
  script: VideoScript;
  audio_files: TTSResult[];
  media_items: MediaItem[];
}): Promise<VideoResult> {
  const response = await apiClient.post<VideoResult>('/videos/assemble', data);
  return response.data;
}

export function getVideoDownloadUrl(videoId: string): string {
  return `/api/videos/${videoId}/download`;
}

export default apiClient;
