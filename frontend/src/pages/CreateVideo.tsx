import { useState } from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import TopicInput from '../components/TopicInput';
import ScriptEditor from '../components/ScriptEditor';
import MediaPreview from '../components/MediaPreview';
import GenerationProgress from '../components/GenerationProgress';
import VideoPlayer from '../components/VideoPlayer';
import { useVideoGeneration } from '../hooks/useVideoGeneration';
import * as api from '../api/client';
import type { SceneMedia } from '../types';

function getStepNumber(step: string): number {
  switch (step) {
    case 'idle':
    case 'generating_script':
      return 0;
    case 'editing_script':
      return 1;
    case 'sourcing_media':
    case 'editing_media':
      return 2;
    case 'generating_tts':
    case 'assembling':
      return 3;
    case 'complete':
      return 4;
    default:
      return 0;
  }
}

export default function CreateVideo() {
  const {
    step,
    script,
    ttsVoice,
    sceneMedia,
    videoResult,
    error,
    handleGenerateScript,
    handleUpdateScript,
    handleConfirmScript,
    handleConfirmMedia,
    handleRetry,
    handleBack,
    setSceneMedia,
    setAudioResults,
  } = useVideoGeneration();

  const [regeneratingScene, setRegeneratingScene] = useState<number | null>(null);

  const handleRegenerateScene = async (sceneNumber: number) => {
    if (!script) return;
    setRegeneratingScene(sceneNumber);
    try {
      const allMedia = await api.sourceMedia(script);
      const sceneData = allMedia.find((s: SceneMedia) => s.scene_number === sceneNumber);
      if (sceneData) {
        setSceneMedia(
          sceneMedia.map((s: SceneMedia) =>
            s.scene_number === sceneNumber ? sceneData : s,
          ),
        );
      }
    } catch {
      // error handled by api client toast
    } finally {
      setRegeneratingScene(null);
    }
  };

  const currentStepNumber = getStepNumber(step);
  const progressSteps = ['Topic', 'Script', 'Media', 'Generate', 'Result'];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Progress Steps */}
      <div className="mb-10">
        <div className="flex items-center justify-between max-w-lg mx-auto">
          {progressSteps.map((label, index) => (
            <div key={label} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                    index <= currentStepNumber
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-800 text-gray-500 border border-gray-700'
                  }`}
                >
                  {index + 1}
                </div>
                <span className={`text-xs mt-1 ${index <= currentStepNumber ? 'text-primary-400' : 'text-gray-600'}`}>
                  {label}
                </span>
              </div>
              {index < progressSteps.length - 1 && (
                <div
                  className={`w-8 sm:w-16 h-0.5 mx-1 sm:mx-2 ${
                    index < currentStepNumber ? 'bg-primary-600' : 'bg-gray-800'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Error State */}
      {step === 'error' && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-red-300 font-medium">Something went wrong</p>
            <p className="text-red-400/80 text-sm mt-1">{error || 'An unexpected error occurred'}</p>
          </div>
          <button
            onClick={handleRetry}
            className="flex items-center gap-1 px-3 py-1.5 bg-red-800/50 hover:bg-red-800 border border-red-700 rounded-lg text-red-300 text-sm transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Retry
          </button>
        </div>
      )}

      {/* Content Area */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 sm:p-8">
        {(step === 'idle' || step === 'generating_script') && (
          <TopicInput
            onSubmit={handleGenerateScript}
            isLoading={step === 'generating_script'}
          />
        )}

        {(step === 'editing_script' || step === 'sourcing_media') && script && (
          <>
            {step === 'editing_script' && (
              <button
                onClick={handleBack}
                className="mb-4 px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                ← Back to Topic
              </button>
            )}
            <ScriptEditor
              script={script}
              voice={ttsVoice}
              onUpdate={handleUpdateScript}
              onConfirm={handleConfirmScript}
              isLoading={step === 'sourcing_media'}
              onTtsGenerated={setAudioResults}
            />
          </>
        )}

        {step === 'editing_media' && (
          <>
            <button
              onClick={handleBack}
              className="mb-4 px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              ← Back to Script
            </button>
            <MediaPreview
              sceneMedia={sceneMedia}
              onUpdateMedia={setSceneMedia}
              onConfirm={handleConfirmMedia}
              isLoading={regeneratingScene !== null}
              onRegenerateScene={handleRegenerateScene}
              script={script}
            />
          </>
        )}

        {(step === 'generating_tts' || step === 'assembling') && (
          <GenerationProgress step={step} onCancel={handleRetry} />
        )}

        {step === 'complete' && videoResult && (
          <VideoPlayer result={videoResult} onReset={handleRetry} />
        )}
      </div>
    </div>
  );
}
