import { useState, useRef, useCallback, useEffect } from 'react';
import { Plus, Trash2, ArrowRight, Check } from 'lucide-react';
import type { VideoScript, ScriptScene, TTSResult } from '../types';
import VoicePreview from './VoicePreview';

interface ScriptEditorProps {
  script: VideoScript;
  voice?: string;
  onUpdate: (script: VideoScript) => void;
  onConfirm: () => void;
  isLoading: boolean;
  onTtsGenerated?: (results: TTSResult[]) => void;
}

export default function ScriptEditor({ script, voice, onUpdate, onConfirm, isLoading, onTtsGenerated }: ScriptEditorProps) {
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const showSaved = useCallback(() => {
    setSaved(true);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setSaved(false), 1500);
  }, []);

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  const updateScene = (index: number, field: keyof ScriptScene, value: string | number) => {
    const updatedScenes = [...script.scenes];
    updatedScenes[index] = { ...updatedScenes[index], [field]: value };
    const totalDuration = updatedScenes.reduce((sum, s) => sum + s.duration_seconds, 0);
    onUpdate({ ...script, scenes: updatedScenes, total_duration: totalDuration });
    showSaved();
  };

  const addScene = () => {
    const newScene: ScriptScene = {
      scene_number: script.scenes.length + 1,
      narration: '',
      visual_description: '',
      duration_seconds: 10,
    };
    const updatedScenes = [...script.scenes, newScene];
    const totalDuration = updatedScenes.reduce((sum, s) => sum + s.duration_seconds, 0);
    onUpdate({ ...script, scenes: updatedScenes, total_duration: totalDuration });
    showSaved();
  };

  const removeScene = (index: number) => {
    if (script.scenes.length <= 1) return;
    const updatedScenes = script.scenes.filter((_, i) => i !== index);
    const totalDuration = updatedScenes.reduce((sum, s) => sum + s.duration_seconds, 0);
    onUpdate({ ...script, scenes: updatedScenes, total_duration: totalDuration });
    showSaved();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">Edit Script</h3>
          <p className="text-sm text-gray-400">
            {script.scenes.length} scenes - {Math.round(script.total_duration)}s total
          </p>
        </div>
        <div className="flex items-center gap-3">
          {saved && (
            <span className="flex items-center gap-1 text-xs text-green-400 animate-pulse">
              <Check className="w-3 h-3" /> Saved
            </span>
          )}
          <button
            type="button"
            onClick={addScene}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Scene
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {script.scenes.map((scene, index) => (
          <div
            key={index}
            className="p-4 bg-gray-800/50 border border-gray-700 rounded-xl space-y-3"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-primary-400">Scene {index + 1}</span>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-500">Duration (s):</label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={scene.duration_seconds}
                    onChange={(e) => updateScene(index, 'duration_seconds', Number(e.target.value))}
                    className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                </div>
                {script.scenes.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeScene(index)}
                    className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Narration</label>
              <textarea
                value={scene.narration}
                onChange={(e) => updateScene(index, 'narration', e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary-500 resize-none h-20"
                placeholder="What the narrator will say..."
              />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Visual Description</label>
              <textarea
                value={scene.visual_description}
                onChange={(e) => updateScene(index, 'visual_description', e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary-500 resize-none h-16"
                placeholder="Describe what visuals to show..."
              />
            </div>
          </div>
        ))}
      </div>

      <VoicePreview script={script} voice={voice} onGenerated={onTtsGenerated} />

      <button
        type="button"
        onClick={onConfirm}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Sourcing Media...' : 'Continue - Find Media'}
        {!isLoading && <ArrowRight className="w-5 h-5" />}
      </button>
    </div>
  );
}
