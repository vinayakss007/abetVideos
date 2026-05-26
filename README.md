# Abet Videos - AI Video Generator

An AI-powered web application that creates short videos (up to 10 minutes) from a text topic. The pipeline generates a script using an LLM, converts narration to speech, sources relevant stock footage/images/GIFs, and assembles everything into a final video.

## How It Works

```
Topic Input -> AI Script Generation -> Text-to-Speech -> Media Sourcing -> Video Assembly -> Final MP4
```

1. **Script Generation** - An LLM (OpenAI-compatible) creates a structured video script with scenes, narration, and visual descriptions
2. **Text-to-Speech** - edge-tts converts each scene's narration into audio
3. **Media Sourcing** - Searches Pexels, Pixabay, and Giphy for relevant stock videos, images, and GIFs
4. **Video Assembly** - MoviePy + FFmpeg combines audio and visuals into the final video

## Architecture

```
+-------------------+       +-------------------+
|   React Frontend  | <---> |  FastAPI Backend   |
|   (Vite + TS)     |  API  |  (Python 3.11)    |
+-------------------+       +-------------------+
       |                            |
       | Port 3000                  | Port 8000
       |                            |
       |                    +-------+-------+
       |                    |   Services    |
       |                    +---------------+
       |                    | AI Gateway    | -> OpenAI / compatible LLMs
       |                    | Script Gen    | -> Uses AI Gateway
       |                    | TTS Service   | -> edge-tts (free)
       |                    | Media Sourcer | -> Pexels, Pixabay, Giphy
       |                    | Video Assembly| -> MoviePy + FFmpeg
       |                    +---------------+
```

## Quick Start with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/your-username/abetVideos.git
cd abetVideos

# 2. Create your environment file
cp .env.example .env
# Edit .env and add your API keys

# 3. Start the application
docker compose up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Manual Setup

### Prerequisites

- Python 3.11+
- Node.js 22+
- FFmpeg installed and on PATH

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
cd backend
pip install -e '.[dev]'

# Copy and configure environment variables
cp .env.example ../.env

# Run the backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on http://localhost:5173 and proxies API requests to http://localhost:8000.

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | API key for the LLM provider | Yes | - |
| `OPENAI_BASE_URL` | Base URL for the LLM API | No | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model name to use | No | `gpt-4o-mini` |
| `PEXELS_API_KEY` | Pexels API key for stock video/photos | No | - |
| `PIXABAY_API_KEY` | Pixabay API key for stock video/photos | No | - |
| `GIPHY_API_KEY` | Giphy API key for GIFs | No | - |
| `TTS_VOICE` | edge-tts voice name | No | `en-US-AriaNeural` |
| `OUTPUT_DIR` | Directory for generated files | No | `./output` |

At least one media API key (Pexels, Pixabay, or Giphy) is recommended for sourcing visuals.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/videos/generate-script` | Generate a video script from a topic |
| `POST` | `/api/videos/generate-tts` | Generate TTS audio from a script |
| `POST` | `/api/videos/source-media` | Source media for each scene |
| `POST` | `/api/videos/assemble` | Assemble the final video |
| `POST` | `/api/videos/generate-full` | Full pipeline with SSE progress streaming |
| `GET` | `/api/videos/{video_id}/download` | Download a generated video |

### Full Pipeline (SSE)

The `/api/videos/generate-full` endpoint runs the entire pipeline in one call and streams progress via Server-Sent Events:

```bash
curl -N -X POST http://localhost:8000/api/videos/generate-full \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of computers", "duration_minutes": 1.0, "style": "educational"}'
```

Each SSE event has the format:
```json
{"step": "script_generation", "progress": 25, "message": "Script generated...", "data": {...}}
```

Steps: `script_generation` -> `tts_generation` -> `media_sourcing` -> `video_assembly` -> `complete`

## Usage Guide

1. **Enter a topic** - Type any topic you want a video about (e.g., "The solar system explained")
2. **Choose duration** - Select 0.5 to 10 minutes
3. **Pick a style** - Educational, entertaining, documentary, motivational, or news
4. **Generate script** - The AI creates a scene-by-scene script with narration and visual descriptions
5. **Edit script** - Review and modify the generated script as needed
6. **Source media** - The app finds relevant stock footage, images, and GIFs for each scene
7. **Assemble** - The final video is assembled with narration, visuals, and transitions
8. **Download** - Download the completed MP4 video

Alternatively, use the "Full Pipeline" mode to run all steps automatically with real-time progress updates.

## Tech Stack

**Backend:**
- Python 3.11
- FastAPI (web framework)
- OpenAI SDK (LLM integration, supports any compatible provider)
- edge-tts (free text-to-speech)
- MoviePy + FFmpeg (video assembly)
- httpx (async HTTP client for media APIs)
- Pydantic (data validation)

**Frontend:**
- React 19
- TypeScript
- Vite (build tool)
- Tailwind CSS v4 (styling)
- Axios (HTTP client)
- React Router (navigation)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (production frontend serving)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes using conventional commits: `feat:`, `fix:`, `docs:`, etc.
4. Push and open a pull request

## License

MIT
