import { Loader2, Mic, Film, Clapperboard, CheckCircle2, Wand2 } from 'lucide-react';
import type { GenerationStep, AIGenerationStats } from '../types';

interface GenerationProgressProps {
  step: GenerationStep;
  aiStats?: AIGenerationStats | null;
}

const STEPS = [
  { key: 'generating_tts', label: 'Generating Voice-Over', icon: Mic },
  { key: 'assembling', label: 'Assembling Video', icon: Clapperboard },
  { key: 'complete', label: 'Complete', icon: CheckCircle2 },
] as const;

export default function GenerationProgress({ step, aiStats }: GenerationProgressProps) {
  const getCurrentStepIndex = () => {
    return STEPS.findIndex((s) => s.key === step);
  };

  const currentIndex = getCurrentStepIndex();

  return (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600/20 rounded-full mb-4">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        </div>
        <h3 className="text-xl font-semibold text-gray-100">Generating Your Video</h3>
        <p className="text-sm text-gray-400 mt-1">This may take a few minutes depending on video length</p>
      </div>

      <div className="max-w-md mx-auto space-y-4">
        {STEPS.map((s, index) => {
          const Icon = s.icon;
          const isActive = s.key === step;
          const isComplete = index < currentIndex;

          return (
            <div
              key={s.key}
              className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                isActive
                  ? 'bg-primary-600/10 border border-primary-500/30'
                  : isComplete
                  ? 'bg-green-600/10 border border-green-500/20'
                  : 'bg-gray-800/50 border border-gray-700'
              }`}
            >
              <div
                className={`p-2 rounded-lg ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-400'
                    : isComplete
                    ? 'bg-green-600/20 text-green-400'
                    : 'bg-gray-700 text-gray-500'
                }`}
              >
                {isActive ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isComplete ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <Icon className="w-5 h-5" />
                )}
              </div>
              <div className="flex-1">
                <p className={`font-medium ${isActive ? 'text-primary-300' : isComplete ? 'text-green-300' : 'text-gray-500'}`}>
                  {s.label}
                </p>
              </div>
              {isActive && (
                <Film className="w-4 h-4 text-primary-400 animate-pulse" />
              )}
            </div>
          );
        })}
      </div>

      <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-primary-600 to-blue-600 rounded-full transition-all duration-1000"
          style={{ width: `${Math.max(((currentIndex + 1) / STEPS.length) * 100, 10)}%` }}
        />
      </div>

      {aiStats && (aiStats.ai_image_limit > 0 || aiStats.ai_video_limit > 0) && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-600/10 border border-purple-500/30">
            <Wand2 className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-sm text-purple-300">
              AI Generated: {aiStats.ai_images_generated}/{aiStats.ai_image_limit} images
              {aiStats.ai_video_limit > 0 && (
                <>, {aiStats.ai_videos_generated}/{aiStats.ai_video_limit} videos</>
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
