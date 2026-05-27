# Test Runs: AI Video Generation Pipeline

## Test 2: Full Pipeline (2025-05-27)

**File:** `demo/ai-full-pipeline-test.mp4`

| Property   | Value                      |
|------------|----------------------------|
| Topic      | 5 Ways AI is Changing the World |
| Duration   | 25.5 seconds               |
| Resolution | 1920x1080 (Full HD)        |
| Codec      | H.264 video, AAC audio     |
| FPS        | 24                         |
| File size  | 2.6 MB                     |
| Scenes     | 3 scenes with TTS narration + Pexels stock footage |

### Pipeline Steps (all successful)

1. **Script** - Pre-written 3-scene script (OpenRouter DNS blocked in test sandbox)
2. **TTS (edge-tts)** - Real speech synthesis for all 3 scenes
3. **Media sourcing (Pexels API)** - Real API calls, downloaded HD stock videos
4. **Video assembly (MoviePy+FFmpeg)** - Combined audio + visuals into final MP4

### What was tested
- edge-tts generates real audio (no mocks)
- Pexels API returns real HD stock footage (videos + images)
- MoviePy assembles scenes with audio sync
- Fallback text-on-background works for scenes without stock matches
- AI generation settings respected (disabled for this test)
- Local library provider checked first (empty, fell through to Pexels)

---

## Test 1: Initial Pipeline (2025-05-26)

**File:** `demo/ai-demo-30sec.mp4`

| Property   | Value                      |
|------------|----------------------------|
| Topic      | The Rise of Artificial Intelligence |
| Duration   | 27.9 seconds               |
| Resolution | 1920x1080 (Full HD)        |
| Codec      | H.264 video, AAC audio     |
| FPS        | 24                         |
| File size  | 9.4 MB                     |
| Bitrate    | 2820 kbps                  |
| Scenes     | 3 scenes with narration and stock footage from Pexels |

### Pipeline Steps (all successful)

1. **Script creation** - Generated a 3-scene narration script about AI
2. **TTS (edge-tts)** - Converted narration text to speech audio
3. **Media sourcing (Pexels)** - Downloaded relevant stock footage for each scene
4. **Video assembly (MoviePy+FFmpeg)** - Combined audio and video into final output
