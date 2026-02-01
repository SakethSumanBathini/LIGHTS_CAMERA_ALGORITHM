"""
AI Modules for SceneSense AI
"""

from .narrative_memory import (
    get_embedder,
    extract_text_from_pdf,
    chunk_script,
    build_memory_index,
    retrieve_context,
    format_context_for_prompt
)

from .scene_director import (
    safe_get,
    clamp_intensity,
    clamp_confidence,
    normalize_hex,
    extract_json_loose,
    build_prompt,
    analyze_scene
)

from .scene_risk_analyzer import analyze_scene_risk

from .shot_image_generator import (
    NanoBananaGenerator,
    CinematicPromptBuilder,
    GEMINI_AVAILABLE,
)

__all__ = [
    'get_embedder',
    'extract_text_from_pdf',
    'chunk_script',
    'build_memory_index',
    'retrieve_context',
    'format_context_for_prompt',
    'safe_get',
    'clamp_intensity',
    'clamp_confidence',
    'normalize_hex',
    'extract_json_loose',
    'build_prompt',
    'analyze_scene',
    'analyze_scene_risk',
    'NanoBananaGenerator',
    'CinematicPromptBuilder',
    'GEMINI_AVAILABLE',
]
