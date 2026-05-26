import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { getScenes } from '../api/client';
import { useEditor } from '../hooks/useEditor';
import type { SceneMetadata } from '../types';
import SceneTimeline from '../components/editor/SceneTimeline';
import SceneTrimmer from '../components/editor/SceneTrimmer';
import TextOverlayEditor from '../components/editor/TextOverlayEditor';
import MediaSwapPanel from '../components/editor/MediaSwapPanel';
import AudioControls from '../components/editor/AudioControls';
import PreviewPanel from '../components/editor/PreviewPanel';

export default function EditorPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const editor = useEditor();

  useEffect(() => {
    if (!videoId) return;

    // Reset immediately and synchronously before starting the new load
    // to prevent stale state from previous videoId interfering.
    editor.reset();

    let cancelled = false;

    async function loadScenes() {
      setIsLoading(true);
      setLoadError(null);
      try {
        const scenes = await getScenes(videoId!);
        if (!cancelled) {
          editor.setScenes(scenes);
        }
      } catch {
        if (!cancelled) {
          setLoadError('Failed to load scenes for this video.');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadScenes();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId]);

  const handleSave = async () => {
    if (!videoId) return;
    const result = await editor.submitEdits(videoId);
    if (result) {
      toast.success('Edits saved successfully!');
    }
  };

  const selectedScene: SceneMetadata | undefined = editor.scenes[editor.selectedSceneIndex];
  const selectedTrim = selectedScene
    ? editor.editInstructions.trims.find((t) => t.scene_number === selectedScene.scene_number)
    : undefined;
  const selectedAudioLevel = selectedScene
    ? editor.editInstructions.audio_levels.find((a) => a.scene_number === selectedScene.scene_number)
    : undefined;

  // Compute the absolute start offset for the selected scene in the source video
  const sceneStartOffset = (() => {
    if (!selectedScene) return 0;
    let offset = 0;
    for (const s of editor.scenes) {
      if (s.scene_number === selectedScene.scene_number) break;
      offset += s.duration_seconds;
    }
    return offset;
  })();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
          <p className="text-gray-400 text-sm">Loading editor...</p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <p className="text-red-400">{loadError}</p>
          <Link to="/" className="text-primary-400 hover:text-primary-300 text-sm underline">
            Go back
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back</span>
          </Link>
          <h1 className="text-xl font-semibold text-gray-100">Video Editor</h1>
          {editor.isDirty && (
            <span className="text-xs text-yellow-400 bg-yellow-400/10 px-2 py-0.5 rounded">Unsaved</span>
          )}
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={editor.isSubmitting || !editor.isDirty}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:opacity-50 text-white font-medium rounded-lg transition-all"
        >
          {editor.isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Edits
        </button>
      </div>

      {/* Timeline */}
      <div className="bg-gray-900 rounded-xl border border-gray-700">
        <SceneTimeline
          scenes={editor.scenes}
          selectedIndex={editor.selectedSceneIndex}
          onSelect={editor.selectScene}
          onReorder={editor.reorderScenes}
        />
      </div>

      {/* Editor panels */}
      {selectedScene && videoId && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SceneTrimmer
            scene={selectedScene}
            trim={selectedTrim}
            onTrimChange={(start, end) => editor.updateTrim(selectedScene.scene_number, start, end)}
          />
          <AudioControls
            sceneNumber={selectedScene.scene_number}
            volume={selectedAudioLevel?.volume ?? 1.0}
            bgMusicVolume={editor.editInstructions.background_music_volume}
            onVolumeChange={(v) => editor.setAudioLevel(selectedScene.scene_number, v)}
            onBgMusicVolumeChange={editor.setBgMusicVolume}
          />
          <TextOverlayEditor
            scene={selectedScene}
            sceneNumber={selectedScene.scene_number}
            overlays={editor.editInstructions.text_overlays}
            onAdd={editor.addOverlay}
            onRemove={editor.removeOverlay}
            onUpdate={editor.updateOverlay}
          />
          <MediaSwapPanel
            sceneNumber={selectedScene.scene_number}
            currentMediaUrl={selectedScene.media_url}
            onSwap={(url, mediaType) => {
              editor.swapMedia(selectedScene.scene_number, url, mediaType);
            }}
          />
          <PreviewPanel
            videoId={videoId}
            sceneNumber={selectedScene.scene_number}
            scene={selectedScene}
            sceneStartOffset={sceneStartOffset}
          />
        </div>
      )}
    </div>
  );
}
