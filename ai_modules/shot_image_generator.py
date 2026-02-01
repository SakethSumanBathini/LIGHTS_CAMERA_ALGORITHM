"""
🎬 SceneSense AI — Shot Image Generator (Gemini Nano Banana)
=============================================================
FIXED: Uses google-genai SDK with response_modalities=["IMAGE"]
NOT the old google-generativeai response_mime_type approach.

Generates cinematic shot visualizations using:
  • Gemini 2.5 Flash Image (gemini-2.5-flash-image) — Nano Banana
  • FREE tier: ~500 images/day via Google AI Studio key

Setup:
    pip install google-genai Pillow
    Set GEMINI_API_KEY in .env (free at aistudio.google.com)
"""

import os
import io
import base64
import hashlib
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── SDK imports ─────────────────────────────────────────────────────────────

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CINEMATIC PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class CinematicPromptBuilder:
    """Translate shot metadata into rich image-generation prompts."""

    SHOT_MAP = {
        "wide":           "extremely wide angle establishing shot, full environment visible",
        "establishing":   "ultra-wide establishing shot showing entire location",
        "medium":         "medium shot from waist up, character in environment",
        "close-up":       "tight close-up on face, shallow depth of field",
        "close up":       "tight close-up on face, shallow depth of field",
        "extreme close":  "extreme macro close-up filling the frame",
        "ots":            "over-the-shoulder two-person framing",
        "over the shoulder": "over-the-shoulder two-person framing",
        "low angle":      "dramatic low angle looking up, powerful imposing",
        "high angle":     "high angle looking down, vulnerability",
        "dutch":          "tilted dutch angle, unease and tension",
        "pov":            "first-person POV subjective camera",
        "tracking":       "dynamic tracking shot with motion",
        "drone":          "aerial drone shot, overhead perspective",
        "macro":          "extreme macro detail shot",
        "insert":         "insert detail shot, specific object focus",
    }

    MOOD_MAP = {
        "tense":       "dramatic shadows, uncomfortable close framing, tension",
        "romantic":    "warm soft glow, gentle atmosphere, intimate",
        "dark":        "ominous deep shadows, foreboding, noir",
        "hopeful":     "light breaking through, uplifting warm tones",
        "chaotic":     "frantic energy, motion blur, disorienting",
        "eerie":       "fog, partial visibility, uncanny atmosphere",
        "peaceful":    "calm serene balanced composition, gentle light",
        "urgent":      "fast-paced, motion blur, high energy",
        "mysterious":  "haze, silhouettes, enigmatic lighting",
        "suspense":    "high contrast, deep blacks, paranoid framing",
    }

    def build(self, shot: Dict, scene_context: Dict = None) -> str:
        parts = [
            "Generate a cinematic film still, photorealistic movie scene",
            "professional cinematography, 35mm film look, anamorphic lens",
            "movie color grading, production quality, no text overlays"
        ]

        # Shot type
        stype = str(shot.get("shot_type", "medium")).lower()
        matched = False
        for key, desc in self.SHOT_MAP.items():
            if key in stype:
                parts.append(desc)
                matched = True
                break
        if not matched:
            parts.append(f"{stype} shot")

        # Purpose / description
        purpose = shot.get("purpose", "")
        if purpose:
            parts.append(purpose)

        # Framing
        framing = shot.get("framing", "")
        if framing and framing != "—":
            parts.append(f"Framing: {framing}")

        # Camera movement feel
        move = shot.get("camera_movement", "")
        if move and move != "—":
            parts.append(f"Camera feel: {move}")

        # Scene context enrichment
        if scene_context:
            mood = str(scene_context.get("visual_mood", "")).lower()
            for key, desc in self.MOOD_MAP.items():
                if key in mood:
                    parts.append(desc)
                    break

            emotion = scene_context.get("emotion", "")
            if emotion:
                parts.append(f"emotional tone: {emotion}")

            palette = scene_context.get("color_palette", [])
            if isinstance(palette, list) and palette:
                colors = [str(c.get("name", "")) for c in palette[:3] if isinstance(c, dict)]
                if colors:
                    parts.append(f"color palette: {', '.join(colors)}")

        # Lighting
        light = shot.get("lighting", "")
        if light and light != "—":
            parts.append(f"Lighting: {light}")

        # Quality suffix
        parts.append("4K ultra-detailed, depth of field, volumetric lighting, cinematic aspect ratio")

        return ". ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# NANO BANANA IMAGE GENERATOR — FIXED API
# ═══════════════════════════════════════════════════════════════════════════════

class NanoBananaGenerator:
    """
    Generate shot images via Gemini 2.5 Flash Image (Nano Banana).
    
    USES the correct google-genai SDK:
        from google import genai
        client = genai.Client(api_key=...)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],  # ← THIS IS THE FIX
            ),
        )
    
    NOT the old google.generativeai GenerativeModel approach with
    response_mime_type="image/png" which causes the 400 error.
    """

    MODEL_ID = "gemini-2.5-flash-image"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.prompt_builder = CinematicPromptBuilder()
        self.cache_dir = Path("./image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._client = None
        self._ready = False

        if self.api_key and GEMINI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=self.api_key)
                self._ready = True
            except Exception as e:
                print(f"[NanoBanana] Client init error: {e}")

    @property
    def is_available(self) -> bool:
        return self._ready and GEMINI_AVAILABLE and self._client is not None

    def generate_for_shot(
        self,
        shot: Dict,
        scene_context: Dict = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a cinematic image for one shot.
        Called ONLY when user clicks the Analyze button.
        Includes retry with exponential backoff for rate limits.
        """
        if not self.is_available:
            return {
                "image_base64": None,
                "error": "Gemini not configured. Add GEMINI_API_KEY in sidebar or install: pip install google-genai",
                "prompt_used": "",
            }

        prompt = self.prompt_builder.build(shot, scene_context)

        # ── Cache check ──
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:16]
        cache_path = self.cache_dir / f"{cache_key}.png"

        if use_cache and cache_path.exists():
            with open(cache_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            return {
                "image_base64": img_b64,
                "prompt_used": prompt,
                "cached": True,
                "error": None,
            }

        # ── Generate via Gemini with retry ──
        import time as _time
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.MODEL_ID,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                    ),
                )

                # Extract image from response parts
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            img_bytes = part.inline_data.data
                            if isinstance(img_bytes, str):
                                img_bytes = base64.b64decode(img_bytes)

                            # Save to cache
                            with open(cache_path, "wb") as f:
                                f.write(img_bytes)

                            return {
                                "image_base64": base64.b64encode(img_bytes).decode(),
                                "prompt_used": prompt,
                                "cached": False,
                                "error": None,
                            }

                # Check for text-only response
                text_parts = []
                if response.candidates and response.candidates[0].content:
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            text_parts.append(part.text)

                if text_parts:
                    return {
                        "image_base64": None,
                        "prompt_used": prompt,
                        "error": f"Model returned text instead of image: {text_parts[0][:200]}",
                    }

                return {
                    "image_base64": None,
                    "prompt_used": prompt,
                    "error": "No image data in response. Try rephrasing the shot description.",
                }

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg

                # Retry on rate limit errors
                if any(k in error_msg.upper() for k in ["QUOTA", "RATE", "429", "RESOURCE_EXHAUSTED"]):
                    if attempt < max_retries - 1:
                        wait = (attempt + 1) * 15  # 15s, 30s, 45s
                        _time.sleep(wait)
                        continue

                # Provide friendly error messages for non-retryable errors
                if "SAFETY" in error_msg.upper() or "BLOCKED" in error_msg.upper():
                    last_error = "Image blocked by safety filter. Try a different shot description."
                elif "API_KEY" in error_msg.upper() or "401" in error_msg or "403" in error_msg:
                    last_error = "Invalid API key. Check your Gemini key in the sidebar."
                break

        # All retries exhausted
        if any(k in last_error.upper() for k in ["QUOTA", "RATE", "429", "RESOURCE_EXHAUSTED"]):
            last_error = "Rate limit reached after 3 retries. Wait 1-2 minutes and try again. (Free tier: 5-15 requests/min)"

        return {
            "image_base64": None,
            "prompt_used": prompt,
            "error": last_error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎬 Shot Image Generator — Gemini Nano Banana (FIXED)")
    print(f"   google-genai SDK: {GEMINI_AVAILABLE}")
    print(f"   API key set:      {bool(os.getenv('GEMINI_API_KEY'))}")
    print(f"   PIL available:    {PIL_AVAILABLE}")

    builder = CinematicPromptBuilder()
    test = builder.build(
        {"shot_type": "Low Angle", "purpose": "Show hero determination",
         "lighting": "Rim lighting", "camera_movement": "Dolly forward"},
        {"visual_mood": "tense dark", "emotion": "tension",
         "color_palette": [{"name": "Electric Teal"}, {"name": "Deep Violet"}]}
    )
    print(f"\n   Prompt ({len(test)} chars):\n   {test[:300]}...")
    print("\n   ✅ Module ready — uses response_modalities=['IMAGE']")
