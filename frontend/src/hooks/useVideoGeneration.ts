import { useState, useCallback, useRef } from 'react';
import type {
  VideoRequest,
  VideoScript,
  MediaItem,
  TTSResult,
  VideoResult,
  GenerationStep,
} from '../types';
import * as api from '../api/client';

export interface SSEProgress {
  step: string;
  progress: number;
  message: string;
  data?: unknown;
}

interface UseVideoGenerationReturn {
  step: GenerationStep;
  script: VideoScript | null;
  mediaItems: MediaItem[];
  audioResults: TTSResult[];
  videoResult: VideoResult | null;
  error: string | null;
  sseProgress: SSEProgress | null;
  handleGenerateScript: (request: VideoRequest) => Promise<void>;
  handleUpdateScript: (script: VideoScript) => void;
  handleConfirmScript: () => Promise<void>;
  handleConfirmMedia: () => Promise<void>;
  handleRetry: () => void;
  generateFull: (request: VideoRequest) => Promise<void>;
  setMediaItems: (items: MediaItem[]) => void;
  setStep: (step: GenerationStep) => void;
}

export function useVideoGeneration(): UseVideoGenerationReturn {
  const [step, setStep] = useState<GenerationStep>('idle');
  const [script, setScript] = useState<VideoScript | null>(null);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [audioResults, setAudioResults] = useState<TTSResult[]>([]);
  const [videoResult, setVideoResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sseProgress, setSSEProgress] = useState<SSEProgress | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleGenerateScript = useCallback(async (request: VideoRequest) => {
    try {
      setStep('generating_script');
      setError(null);
      const generatedScript = await api.generateScript(request);
      setScript(generatedScript);
      setStep('editing_script');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate script';
      setError(message);
      setStep('error');
    }
  }, []);

  const handleUpdateScript = useCallback((updatedScript: VideoScript) => {
    setScript(updatedScript);
  }, []);

  const handleConfirmScript = useCallback(async () => {
    if (!script) return;
    try {
      setStep('sourcing_media');
      setError(null);
      const media = await api.sourceMedia(script);
      setMediaItems(media);
      setStep('editing_media');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to source media';
      setError(message);
      setStep('error');
    }
  }, [script]);

  const handleConfirmMedia = useCallback(async () => {
    if (!script) return;
    try {
      setStep('generating_tts');
      setError(null);
      const audio = await api.generateTTS(script);
      setAudioResults(audio);

      setStep('assembling');
      const result = await api.assembleVideo({
        script,
        audio_files: audio,
        media_items: mediaItems,
      });
      setVideoResult(result);
      setStep('complete');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate video';
      setError(message);
      setStep('error');
    }
  }, [script, mediaItems]);

  const generateFull = useCallback(async (request: VideoRequest) => {
    try {
      setStep('generating_script');
      setError(null);
      setSSEProgress(null);

      abortRef.current = new AbortController();

      const response = await fetch('/api/videos/generate-full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            try {
              const event: SSEProgress = JSON.parse(jsonStr);
              setSSEProgress(event);

              // Map SSE steps to generation steps
              switch (event.step) {
                case 'script_generation':
                  setStep('generating_script');
                  if (event.data && typeof event.data === 'object' && 'title' in event.data) {
                    setScript(event.data as VideoScript);
                  }
                  break;
                case 'tts_generation':
                  setStep('generating_tts');
                  break;
                case 'media_sourcing':
                  setStep('sourcing_media');
                  break;
                case 'video_assembly':
                  setStep('assembling');
                  break;
                case 'complete':
                  if (event.data) {
                    setVideoResult(event.data as VideoResult);
                  }
                  setStep('complete');
                  break;
                case 'error':
                  setError(event.message);
                  setStep('error');
                  break;
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      const message = err instanceof Error ? err.message : 'Full pipeline failed';
      setError(message);
      setStep('error');
    }
  }, []);

  const handleRetry = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setError(null);
    setStep('idle');
    setScript(null);
    setMediaItems([]);
    setAudioResults([]);
    setVideoResult(null);
    setSSEProgress(null);
  }, []);

  return {
    step,
    script,
    mediaItems,
    audioResults,
    videoResult,
    error,
    sseProgress,
    handleGenerateScript,
    handleUpdateScript,
    handleConfirmScript,
    handleConfirmMedia,
    handleRetry,
    generateFull,
    setMediaItems,
    setStep,
  };
}
