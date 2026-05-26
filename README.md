# ABet Videos

An AI-powered faceless video generation platform that leverages open-source AI tools to automate the entire video creation pipeline -- from script generation to final assembly.

## Overview

ABet Videos aims to build a complete video generation workflow using open-source and freely available AI tools. The goal is to enable creators to produce high-quality faceless videos without manual editing, stock footage subscriptions, or expensive proprietary platforms.

The pipeline automates:

- Script and scene prompt generation
- Realistic voiceover synthesis
- AI-driven video and image generation
- Timeline assembly and editing

Users retain full control with the ability to review, edit, and override any step in the process.

## Architecture / Workflow

The video generation pipeline consists of four core stages:

### 1. Script Generation

AI language models generate structured video scripts complete with scene-by-scene prompts, narration text, and timing cues.

**Tools:**

- [OpenAI ChatGPT](https://chat.openai.com/) - Script writing, scene breakdowns, and prompt engineering
- [Google AI Studio](https://aistudio.google.com/) - Alternative script and prompt generation

### 2. Voiceover / Text-to-Speech (TTS)

Generated scripts are converted into realistic voiceovers using open-source TTS models or free-tier cloud services.

**Tools:**

- [Coqui TTS](https://github.com/coqui-ai/TTS) - Open-source, locally-run text-to-speech with multiple voice models
- [Bark](https://github.com/suno-ai/bark) - Transformer-based generative audio model supporting speech, music, and sound effects
- [ElevenLabs](https://elevenlabs.io/) - High-quality AI voice synthesis (free tier available)

### 3. Video / Image Generation

Instead of relying on stock footage, AI models generate video clips and images directly from script prompts.

**Models:**

| Model | Developer | Description |
|-------|-----------|-------------|
| [HunyuanVideo](https://github.com/Tencent/HunyuanVideo) | Tencent | High-quality open-source video generation model |
| [Mochi 1](https://github.com/genmoai/mochi) | Genmo | Powerful open-source video generation |
| [Wan 2.2](https://github.com/Wan-Video/Wan2.2) | Wan Video | State-of-the-art open-source video synthesis |

**Local Setup:**

- [Pinocchio](https://pinocchio.computer/) - One-click installer for running open-source AI models locally on systems with a dedicated NVIDIA GPU

### 4. Video Editing / Assembly

The final stage combines generated video clips, voiceover audio, subtitles, and transitions into a polished output video.

**Alternative Platforms (for reference):**

- [Pictory AI](https://pictory.ai/) - Turns scripts and blog posts into summarized videos with stock footage and AI voiceovers
- [VEED.IO](https://www.veed.io/) - Browser-based text-to-video, subtitles, and character generation
- [HeyGen](https://www.heygen.com/) - Human-like avatar generation and audio synthesis for faceless content

## Prerequisites

Before setting up the project, ensure you have the following:

- **Operating System:** Linux, macOS, or Windows
- **GPU:** NVIDIA GPU with CUDA support (recommended for local video generation)
  - Minimum: 8 GB VRAM for smaller models
  - Recommended: 16+ GB VRAM for HunyuanVideo, Wan 2.2
- **Python:** 3.9 or higher
- **Node.js:** 18.x or higher (if using web-based tooling)
- **Git:** For cloning repositories and managing dependencies
- **FFmpeg:** For audio/video processing and assembly
- **CUDA Toolkit:** Compatible version for your GPU and chosen models

## Getting Started

1. **Clone the repository:**

   ```bash
   git clone https://github.com/vinayakss007/abetVideos.git
   cd abetVideos
   ```

2. **Review the research notes:**

   Check `imp.md` for detailed notes on available tools and workflow options.

3. **Set up local AI models (using Pinocchio):**

   If you have a compatible NVIDIA GPU, install [Pinocchio](https://pinocchio.computer/) for one-click setup of video generation models like HunyuanVideo, Mochi 1, or Wan 2.2.

4. **Set up TTS:**

   Install Coqui TTS or Bark for local voiceover generation:

   ```bash
   pip install TTS
   ```

   Or for Bark:

   ```bash
   pip install git+https://github.com/suno-ai/bark.git
   ```

5. **Install FFmpeg:**

   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows (via Chocolatey)
   choco install ffmpeg
   ```

6. **Configure API keys (optional):**

   If using cloud-based services like ElevenLabs or OpenAI, set up your API keys as environment variables:

   ```bash
   export OPENAI_API_KEY="your-key-here"
   export ELEVENLABS_API_KEY="your-key-here"
   ```

## Project Structure

```
abetVideos/
├── README.md          # Project documentation
├── imp.md             # Research notes and tool references
└── ...                # Additional modules (coming soon)
```

## Contributing

Contributions are welcome! Here is how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m "feat: add your feature"`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

### Guidelines

- Follow existing code style and conventions
- Write clear commit messages with type prefixes (`feat:`, `fix:`, `docs:`, etc.)
- Include documentation for new features
- Test your changes before submitting

## License

This project is currently unlicensed. A license will be added in the future.

---

*ABet Videos - Let AI do the heavy lifting so you can focus on creativity.*
