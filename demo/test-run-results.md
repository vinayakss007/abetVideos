# Test Run: 30-Second AI Video Generation

**Date:** 2025-05-26

## Video Details

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

## Pipeline Steps (all successful)

1. **Script creation** - Generated a 3-scene narration script about AI
2. **TTS (edge-tts)** - Converted narration text to speech audio
3. **Media sourcing (Pexels)** - Downloaded relevant stock footage for each scene
4. **Video assembly (MoviePy+FFmpeg)** - Combined audio and video into final output

## Notes

- AI keyword extraction fell back to stopword-based extraction since no LLM key was configured at the time of this test
- Video was assembled at 1920x1080 landscape format with 24fps
- Each scene paired narration audio with matching stock video clips
