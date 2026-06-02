
# Abet Videos — Future Plan & Improvement Roadmap

## Priority Legend
- **P0 (Critical):** Security, data loss, or broken core flow
- **P1 (High):** Major UX friction or missing essential features
- **P2 (Medium):** Polish, quality-of-life, code hygiene
- **P3 (Low):** Nice-to-have, long-term

---

## 1. Security (P0)

### 1.1 Harden JWT secret
- **Problem:** `config.py` defaults to `"change-me-to-a-secure-random-string-at-least-32-chars"`. The `.env` has a placeholder `abet-videos-dev-secret-key-change-in-production`.
- **Fix:** Generate a strong random secret at first startup. Fail loudly if the default is unchanged. Store in a file outside the repo.

### 1.2 Move auth token from localStorage to httpOnly cookie
- **Problem:** JWT stored in `localStorage` → XSS vulnerability. Any injected script can steal the token.
- **Fix:** Switch to httpOnly cookies set by the backend. The frontend should never see the raw JWT.

### 1.3 Rate-limit login endpoint
- **Problem:** No brute-force protection. An attacker can try passwords indefinitely.
- **Fix:** Add account lockout after N failed attempts. Use `slowapi` or Redis-based rate limiter.

### 1.4 Replace raw path parameter in audio-download
- **Problem:** `GET /api/videos/audio-download?path=...` accepts an arbitrary filesystem path with only a `relative_to` check that can be bypassed via symlinks.
- **Fix:** Use opaque scene/video IDs and a server-side path map.

### 1.5 CORS restriction in production
- **Problem:** `allow_origins=["*"]` allows any domain to call the API.
- **Fix:** Restrict to the specific frontend domain in production environments.

### 1.6 Mask API keys completely from frontend
- **Problem:** Settings endpoint returns masked keys (e.g., `sk-****abcd`) but the frontend can POST them back, potentially overwriting real keys with masked garbage.
- **Fix:** Skip update when a submitted value matches the masked pattern. Never expose any part of the key to the frontend — return only a boolean `configured` flag.

### 1.7 Set explicit bcrypt rounds
- **Problem:** `bcrypt.gensalt()` uses the library default, which may change.
- **Fix:** Explicitly use `bcrypt.gensalt(rounds=12)`.

---

## 2. Backend / API Reliability (P0–P1)

### 2.1 File-locking for JSON storage
- **Problem:** `settings_manager.py`, `history_service.py`, `auth_service.py` read/write flat JSON files without locking. Concurrent requests from the same user cause race conditions and data corruption.
- **Fix:** Add `fcntl.flock` or `portalocker` for file-level locking. Better yet, migrate to SQLite.

### 2.2 Move `users.json` out of the app package
- **Problem:** `users.json` lives inside `backend/app/`, so it gets overwritten on every deploy.
- **Fix:** Move to `backend/data/users.json` and ensure the directory is volume-mounted in Docker.

### 2.3 Request body size limits
- **Problem:** No global limit on request body size. A large script payload could cause memory exhaustion.
- **Fix:** Add FastAPI middleware to limit request body size (e.g., 10 MB).

### 2.4 Health endpoint should check dependencies
- **Problem:** `GET /health` returns `{"status": "ok"}` without verifying FFmpeg availability, disk space, or API key configuration.
- **Fix:** Add checks for FFmpeg binary, writable disk space, and critical API keys.

### 2.5 Add request correlation IDs
- **Problem:** No request ID in logs, making it hard to trace a single request across services.
- **Fix:** Add middleware that injects a `X-Request-ID` header and includes it in all log lines.

### 2.6 Shared HTTP client pool
- **Problem:** `media_sourcer.py`, `videos.py`, and other services create a new `httpx.AsyncClient()` on every call.
- **Fix:** Use a single shared client instance at the app level with connection pooling.

---

## 3. UI/UX Improvements (P1–P2)

### 3.1 Add navigation back through wizard steps
- **Problem:** On the Create page, users cannot go back to change the topic or edit previous steps. They must abort and start over.
- **Fix:** Add "Back" buttons at each step (ScriptEditor → TopicInput, MediaPreview → ScriptEditor, etc.) with state persistence.

### 3.2 Wire up dead UI buttons
- **Problem:** `MediaPreview.tsx` has a **Refresh All** button that is hardcoded `disabled` and an **Accept** button with no `onClick` handler.
- **Fix:** Implement refresh (regenerate media for all scenes) and accept (confirm and proceed) or remove the buttons.

### 3.3 Add delete functionality to History
- **Problem:** Users can view history but cannot delete individual entries. The `Trash2` icon is imported but never used.
- **Fix:** Add per-entry delete button with confirmation dialog, plus a "Clear All" option.

### 3.4 Fix silent error swallowing on HomePage and History
- **Problem:** `HomePage.tsx` and `History.tsx` use `.catch(() => {})` when fetching history. On failure, users see an incorrect empty state.
- **Fix:** Add error state with a retry button and error message.

### 3.5 Add loading skeletons to Dashboard
- **Problem:** HomePage dashboard shows stat cards with `0` while history is loading.
- **Fix:** Show skeleton/pulsing placeholders during data fetch.

### 3.6 Add "Confirm Password" field on signup
- **Problem:** Signup page has a single password field. Users can mistype and lock themselves out.
- **Fix:** Add a second password confirmation field with client-side matching validation.

### 3.7 Add password strength indicator
- **Problem:** No visible password requirements or strength meter.
- **Fix:** Show minimum length (6+ chars) and a strength bar.

### 3.8 Add character count to topic textarea
- **Problem:** API enforces 500-character limit but the UI doesn't show the count.
- **Fix:** Add a live character counter below the textarea.

### 3.9 Add "Saved" indicator to script editor
- **Problem:** Script editor auto-saves with no visual feedback. Users don't know if their edits persisted.
- **Fix:** Show a subtle "Saved" badge/toast after auto-save completes.

---

## 4. Performance (P1–P2)

### 4.1 Parallelize TTS generation
- **Problem:** TTS is generated sequentially per scene with a 0.5s sleep between each. A 10-scene video wastes 5s of idle time.
- **Fix:** Use `asyncio.gather()` with a semaphore (e.g., 3 concurrent) to generate TTS in parallel.

### 4.2 Eliminate duplicate TTS generation
- **Problem:** `VoicePreview` calls `generateTTS()` independently to preview audio. The same TTS is generated again during assembly, doubling API usage.
- **Fix:** Cache/reuse TTS results from the preview step. Pass the existing audio paths forward.

### 4.3 Offload full assembly to thread pool
- **Problem:** While `write_videofile` is offloaded via `asyncio.to_thread`, the scene clip building and audio processing before it runs on the event loop.
- **Fix:** Offload the entire assembly pipeline to a `concurrent.futures.ProcessPoolExecutor`.

### 4.4 Optimize gradient background generation
- **Problem:** `media_sourcer.py` draws gradient backgrounds pixel-by-pixel using a loop with `draw.line()`. For 1920×1080, that's 1080 draw calls.
- **Fix:** Use `PIL.ImageDraw.rectangle()` with a gradient fill or numpy arrays.

### 4.5 Add video compression post-processing
- **Problem:** Generated videos are not size-optimized. Large files are slow to download.
- **Fix:** Add an optional compression pass using FFmpeg with CRF-based encoding.

---

## 5. Missing Features (P1–P2)

### 5.1 Task cancellation
- **Problem:** The frontend `abortRef` aborts the SSE connection but the backend task continues running until completion.
- **Fix:** Add `DELETE /api/videos/tasks/{task_id}` that cancels the running asyncio task and cleans up partial output files.

### 5.2 Video deletion with file cleanup
- **Problem:** No way to delete individual history entries or their associated files.
- **Fix:** Add `DELETE /api/videos/history/{entry_id}` that removes the history entry and deletes the video file from disk.

### 5.3 "Forgot Password" flow
- **Problem:** No password reset mechanism. If a user forgets their password, they're locked out.
- **Fix:** Add email-based password reset with a secure token (requires email configuration).

### 5.4 User profile editing
- **Problem:** Users cannot update their name, email, or password after signup.
- **Fix:** Add a profile page under `/settings/profile` with edit capabilities.

### 5.5 Video thumbnails
- **Problem:** History shows only text. No visual preview of completed videos.
- **Fix:** Generate a thumbnail frame during assembly and serve it alongside history entries.

### 5.6 Regenerate individual scene media
- **Problem:** Users can search media per scene but cannot regenerate all media for a specific scene with one click.
- **Fix:** Add a "Regenerate" button per scene in MediaPreview that re-sources media for that scene only.

---

## 6. Code Quality & Consistency (P2)

### 6.1 Remove unused imports
- **Files:**
  - `History.tsx`: `Trash2` imported but unused
  - `CreateVideo.tsx`: `audioResults` destructured but unused
  - `MusicBrowser.tsx`: `Search` imported but unused
  - `videos.py` (backend): `httpx` could be scoped better

### 6.2 Standardize error handling
- **Problem:** Mixed patterns — some errors caught specifically, some broadly (`except Exception`), some silently ignored (`.catch(() => {})`).
- **Fix:** Define a consistent error handling strategy with centralized error reporting.

### 6.3 Named constants for magic numbers
- **Values to extract:** `0.5` (TTS sleep), `5` (semaphore), `10` (reconnect attempts), `22050` (sample rate), `0.9` (target peak), `0.3` (ducking ratio)
- **Fix:** Define constants with descriptive names in appropriate modules.

### 6.4 Unify step-by-step and full-pipeline code paths
- **Problem:** Two ways to generate a video (step-by-step API and `/generate-full` with SSE). The step-by-step path lacks SSE progress. Code switches between paths without clear separation.
- **Fix:** Either make all generation use the task manager + SSE, or remove the duplicate path.

### 6.5 Align frontend/backend defaults
- **Problem:** `TopicInput.tsx` sets `background_music_volume: 0.25` but backend `schemas.py` defaults to `0.15`.
- **Fix:** Source defaults from the backend API or keep a single shared constants file.

### 6.6 Add ESLint + Prettier configuration
- **Problem:** `package.json` has `"lint": "eslint ."` but no ESLint config file exists.
- **Fix:** Create proper ESLint + Prettier configuration and fix violations.

### 6.7 Enable strict TypeScript
- **Problem:** TypeScript strict mode is not fully enabled for the main `tsconfig.json`.
- **Fix:** Enable `strict: true` and fix resulting type errors.

---

## 7. Testing (P2–P3)

### 7.1 Unit tests for services
- **Missing tests for:** `tts_service`, `media_sourcer`, `video_assembler`, `audio_processor`, `music_service`, `auth_service`, `settings_manager`, `task_manager`, `history_service`
- **Priority:** `auth_service` and `tts_service` first (most business-critical).

### 7.2 Component tests for critical UI
- **Missing tests for:** `ScriptEditor`, `MediaPreview`, `GenerationProgress`, `History`, `AudioSettings`, `MusicBrowser`, `VoicePreview`, `useVideoGeneration` hook
- **Priority:** `useVideoGeneration` hook and `ScriptEditor` first (core pipeline logic).

### 7.3 Integration tests with real filesystem
- **Problem:** Current tests use mocks. FFmpeg calls, file I/O, and edge-tts are not tested.
- **Fix:** Add integration tests with fixture files and test output directories.

### 7.4 End-to-end test for the full flow
- **Problem:** No Playwright/Cypress test for the complete user journey.
- **Fix:** Add a basic E2E test: login → create topic → edit script → generate video → see in history.

---

## 8. DevOps & Infrastructure (P2–P3)

### 8.1 Docker health checks
- **Problem:** `docker-compose.yml` has no health checks. Frontend `depends_on: backend` is not sufficient.
- **Fix:** Add `healthcheck` blocks for both services.

### 8.2 Persistent volumes for user data
- **Problem:** Docker compose only mounts `./output:/app/output`. User data (`users.json`, settings) lives inside the container.
- **Fix:** Add a volume or bind mount for `backend/data/`.

### 8.3 Add `.dockerignore` files
- **Problem:** No `.dockerignore` for backend or frontend. Build context includes `node_modules`, `.venv`, `.git`, etc.
- **Fix:** Add `.dockerignore` to exclude unnecessary files from Docker builds.

### 8.4 Set up CI/CD pipeline
- **Problem:** No GitHub Actions or other CI pipeline. No automated linting, typecheck, or test execution on push.
- **Fix:** Add a `.github/workflows/ci.yml` that runs lint, typecheck, and tests.

### 8.5 Add structured logging
- **Problem:** Current logging is plain text. Parsing logs in production would be difficult.
- **Fix:** Switch to JSON-formatted logging (e.g., `structlog` or Python's `logging` with JSON formatter).

### 8.6 Add error tracking (Sentry)
- **Problem:** No error monitoring. Backend exceptions and frontend errors are invisible unless the user reports them.
- **Fix:** Integrate Sentry for both frontend and backend.

---

## 9. Long-Term / Strategic (P3)

### 9.1 Migrate from JSON files to a database
- **Problem:** Flat JSON files don't scale, are concurrency-unsafe, and have no migration story.
- **Fix:** Use SQLite for single-server deployments or PostgreSQL for multi-server.

### 9.2 Add media cache database
- **Problem:** `_cache_manifest_lock` in `media_sourcer.py` is per-process. With multiple workers, the cache manifest can corrupt.
- **Fix:** Use SQLite or Redis for the media cache.

### 9.3 Background task queue (Celery / Arq)
- **Problem:** Task manager uses in-memory dict. Server restart loses all running tasks. Long tasks block the event loop.
- **Fix:** Use a proper task queue with persistent storage and worker processes.

### 9.4 Admin dashboard
- **Problem:** No way to manage users, view system metrics, or monitor usage.
- **Fix:** Build a basic admin panel with user management, API key status, and generation metrics.

### 9.5 Add API documentation beyond Swagger
- **Problem:** FastAPI generates Swagger docs, but there's no additional documentation for error codes, rate limits, or authentication flow.
- **Fix:** Add endpoint descriptions, error code references, and usage examples.

### 9.6 Architecture Decision Records (ADRs)
- **Problem:** No documentation explaining why key decisions were made (e.g., JSON vs database, edge-tts vs Google TTS).
- **Fix:** Add ADR documents for major architectural decisions.

---

## Implementation Order (Recommended)

### Phase 1 — Stability & Security (1–2 days)
1. Harden JWT secret
2. File-locking for JSON storage
3. Mask API keys completely
4. Rate-limit login

### Phase 2 — Core UX Fixes (2–3 days)
1. Wire up dead UI buttons (Refresh All, Accept)
2. Add back navigation in Create wizard
3. Fix silent error swallowing on HomePage/History
4. Add delete to History

### Phase 3 — Performance (2–3 days)
1. Parallelize TTS generation
2. Eliminate duplicate TTS generation
3. Task cancellation endpoint

### Phase 4 — Polish (1–2 days)
1. Remove unused imports
2. Align frontend/backend defaults
3. Add loading skeletons
4. Add confirm password, character count, saved indicator

### Phase 5 — Testing & DevOps (ongoing)
1. Add CI pipeline
2. Write unit tests for critical services
3. Add Docker health checks and persistent volumes
