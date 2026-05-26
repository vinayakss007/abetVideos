import { useState, useCallback } from 'react';
import type {
  VideoRequest,
  VideoScript,
  MediaItem,
  TTSResult,
  VideoResult,
  GenerationStep,
} from '../types';
import * as api from '../api/client';

interface UseVideoGenerationReturn {
  step: GenerationStep;
  script: VideoScript | null;
  mediaItems: MediaItem[];
  audioResults: TTSResult[];
  videoResult: VideoResult | null;
  error: string | null;
  handleGenerateScript: (request: VideoRequest) => Promise<void>;
  handleUpdateScript: (script: VideoScript) => void;
  handleConfirmScript: () => Promise<void>;
  handleConfirmMedia: () => Promise<void>;
  handleRetry: () => void;
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

  const handleRetry = useCallback(() => {
    setError(null);
    setStep('idle');
    setScript(null);
    setMediaItems([]);
    setAudioResults([]);
    setVideoResult(null);
  }, []);

  return {
    step,
    script,
    mediaItems,
    audioResults,
    videoResult,
    error,
    handleGenerateScript,
    handleUpdateScript,
    handleConfirmScript,
    handleConfirmMedia,
    handleRetry,
    setMediaItems,
    setStep,
  };
}
