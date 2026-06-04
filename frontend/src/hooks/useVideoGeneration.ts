import { useState, useCallback, useRef } from 'react';
import type {
  VideoRequest,
  VideoScript,
  SceneMedia,
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
  ttsVoice: string;
  sceneMedia: SceneMedia[];
  audioResults: TTSResult[];
  videoResult: VideoResult | null;
  error: string | null;
  sseProgress: SSEProgress | null;
  handleGenerateScript: (request: VideoRequest) => Promise<void>;
  handleUpdateScript: (script: VideoScript) => void;
  handleConfirmScript: () => Promise<void>;
  handleConfirmMedia: () => Promise<void>;
  handleRetry: () => void;
  handleBack: () => void;
  setAudioResults: (results: TTSResult[]) => void;
  generateFull: (request: VideoRequest) => Promise<void>;
  setSceneMedia: (items: SceneMedia[]) => void;
  setStep: (step: GenerationStep) => void;
}

export function useVideoGeneration(): UseVideoGenerationReturn {
  const [step, setStep] = useState<GenerationStep>('idle');
  const [script, setScript] = useState<VideoScript | null>(null);
  const [ttsVoice, setTtsVoice] = useState('en-US-AriaNeural');
  const [sceneMedia, setSceneMedia] = useState<SceneMedia[]>([]);
  const [audioResults, setAudioResults] = useState<TTSResult[]>([]);
  const [videoResult, setVideoResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sseProgress, setSSEProgress] = useState<SSEProgress | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const taskIdRef = useRef<string | null>(null);

  const handleGenerateScript = useCallback(async (request: VideoRequest) => {
    if (request.audio_settings?.tts_voice) {
      setTtsVoice(request.audio_settings.tts_voice);
    }
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
      setSceneMedia(media);
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
      let audio = audioResults;
      if (audio.length === 0) {
        setStep('generating_tts');
        setError(null);
        audio = await api.generateTTS(script);
        setAudioResults(audio);
      }

      setStep('assembling');
      const result = await api.assembleVideo({
        script,
        tts_results: audio,
        scene_media: sceneMedia,
      });
      setVideoResult(result);
      setStep('complete');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate video';
      setError(message);
      setStep('error');
    }
  }, [script, sceneMedia, audioResults]);

  const connectTaskStream = useCallback(async (taskId: string) => {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;

    const connect = async (): Promise<void> => {
      while (reconnectAttempts < maxReconnectAttempts && !abortRef.current?.signal.aborted) {
        try {
          const response = await fetch(`/api/videos/tasks/${taskId}/stream`, {
            credentials: 'include',
            signal: abortRef.current?.signal,
          });

          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) throw new Error('No response stream available');

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
                      return;
                    case 'error':
                      setError(event.message);
                      setStep('error');
                      return;
                  }
                } catch {
                  // Skip malformed JSON lines
                }
              }
            }
          }
          // Stream ended without complete/error, try reconnect
          reconnectAttempts++;
          await new Promise(r => setTimeout(r, 2000));
        } catch (err) {
          if (err instanceof Error && err.name === 'AbortError') return;
          reconnectAttempts++;
          await new Promise(r => setTimeout(r, 2000));
        }
      }
    };

    await connect();
  }, []);

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
        credentials: 'include',
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const { task_id } = await response.json();
      taskIdRef.current = task_id;
      await connectTaskStream(task_id);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      const message = err instanceof Error ? err.message : 'Full pipeline failed';
      setError(message);
      setStep('error');
    }
  }, [connectTaskStream]);

  const handleBack = useCallback(() => {
    setError(null);
    switch (step) {
      case 'editing_script':
      case 'sourcing_media':
        setStep('idle');
        break;
      case 'editing_media':
        setStep('editing_script');
        break;
      case 'generating_tts':
      case 'assembling':
        setStep('editing_media');
        break;
      default:
        break;
    }
  }, [step]);

  const handleRetry = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    const tid = taskIdRef.current;
    if (tid) {
      taskIdRef.current = null;
      api.cancelTask(tid).catch(() => {});
    }
    setError(null);
    setStep('idle');
    setScript(null);
    setSceneMedia([]);
    setAudioResults([]);
    setVideoResult(null);
    setSSEProgress(null);
  }, []);

  return {
    step,
    script,
    ttsVoice,
    sceneMedia,
    audioResults,
    videoResult,
    error,
    sseProgress,
    handleGenerateScript,
    handleUpdateScript,
    handleConfirmScript,
    handleConfirmMedia,
    handleRetry,
    handleBack,
    setAudioResults,
    generateFull,
    setSceneMedia,
    setStep,
  };
}
