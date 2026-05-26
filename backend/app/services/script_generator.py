"""Script generation service using AI gateway."""

import logging
from typing import Optional

from app.models.schemas import VideoScript, VideoStyle
from app.services.ai_gateway import AIGateway, ai_gateway

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional video script writer. Generate engaging video scripts in JSON format.

Your output MUST be valid JSON with this exact structure:
{
  "title": "Video Title",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "The narration text to be spoken aloud for this scene.",
      "visual_description": "A detailed description of what visuals should appear: specific objects, settings, actions that can be searched for as stock footage or images.",
      "duration_seconds": 10.0
    }
  ],
  "total_duration": 60.0
}

Rules:
- Each scene should be 5-30 seconds long
- Narration should be natural, conversational, and engaging
- Visual descriptions should be concrete and searchable (e.g., "aerial view of a city skyline at sunset" not "something cool")
- Total duration should match the requested duration
- Include 3-8 scenes for a 1-minute video, scaling proportionally
- Make the first scene a hook to grab attention
- End with a strong conclusion or call to action
"""


def _build_user_prompt(topic: str, duration_minutes: float, style: VideoStyle) -> str:
    """Build the user prompt for script generation."""
    total_seconds = int(duration_minutes * 60)
    min_scenes = max(3, int(duration_minutes * 3))
    max_scenes = min(30, int(duration_minutes * 8))

    return (
        f"Create a {style.value} video script about: {topic}\n\n"
        f"Requirements:\n"
        f"- Total duration: approximately {total_seconds} seconds ({duration_minutes} minutes)\n"
        f"- Number of scenes: between {min_scenes} and {max_scenes}\n"
        f"- Style: {style.value}\n"
        f"- Make it engaging and informative\n"
        f"- Visual descriptions should be specific enough to search for stock footage\n\n"
        f"Output the script as JSON."
    )


async def generate_script(
    topic: str,
    duration_minutes: float = 1.0,
    style: VideoStyle = VideoStyle.educational,
    gateway: Optional[AIGateway] = None,
) -> VideoScript:
    """Generate a video script using the AI gateway.

    Args:
        topic: The video topic.
        duration_minutes: Desired video duration in minutes.
        style: The video style.
        gateway: Optional AIGateway instance (uses default if not provided).

    Returns:
        A validated VideoScript model.

    Raises:
        ValueError: If the AI response cannot be parsed into a valid script.
    """
    gw = gateway or ai_gateway
    user_prompt = _build_user_prompt(topic, duration_minutes, style)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    logger.info(f"Generating script for topic: '{topic}', duration: {duration_minutes}m")

    response_data = await gw.chat_completion_json(
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
    )

    try:
        script = VideoScript(**response_data)
    except Exception as e:
        logger.error(f"Failed to parse script response: {e}")
        raise ValueError(f"AI response does not match expected script format: {e}") from e

    logger.info(
        f"Generated script: '{script.title}' with {len(script.scenes)} scenes, "
        f"total duration: {script.total_duration}s"
    )

    return script
