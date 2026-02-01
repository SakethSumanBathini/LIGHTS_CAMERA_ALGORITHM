"""
Scene Director Module for SceneSense AI
Converts raw scene text into director-level planning intelligence
"""

import os
import re
import json
import requests
from typing import Any, Dict, Optional
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None


def safe_get(d: Dict[str, Any], key: str, default=None):
    """Safely get a value from a dictionary."""
    v = d.get(key, default)
    return default if v is None else v


def clamp_intensity(x: Any, default: int = 5) -> int:
    """Clamp intensity to 1-10 range."""
    try:
        v = int(x)
        return max(1, min(10, v))
    except Exception:
        return default


def clamp_confidence(x: Any, default: float = 0.75) -> float:
    """Clamp confidence to 0-1 range."""
    try:
        v = float(x)
        return max(0.0, min(1.0, v))
    except Exception:
        return default


def normalize_hex(h: str) -> str:
    """Normalize hex color code."""
    if not h:
        return "#111111"
    h = h.strip()
    if not h.startswith("#"):
        h = "#" + h
    if len(h) == 4:
        h = "#" + "".join([c * 2 for c in h[1:]])
    if len(h) != 7:
        return "#111111"
    return h


def extract_json_loose(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from potentially messy LLM output."""
    if not text:
        return None
    
    text2 = re.sub(r"```(json)?", "", text, flags=re.IGNORECASE).strip("` \n\t")
    
    try:
        return json.loads(text2)
    except Exception:
        pass

    m = re.search(r"\{.*\}", text2, flags=re.DOTALL)
    if not m:
        return None
    blob = m.group(0)
    try:
        return json.loads(blob)
    except Exception:
        blob2 = re.sub(r",(\s*[}\]])", r"\1", blob)
        try:
            return json.loads(blob2)
        except Exception:
            return None


def build_prompt(scene_text: str, mode: str, context_text: str = "") -> str:
    """Build the analysis prompt for the LLM."""
    schema = {
        "mode": "director|writer",
        "emotion": "string",
        "genre": "string",
        "tone": "string",
        "intensity": "integer 1-10",
        "narrative_purpose": "string",
        "visual_mood": "string",
        "camera_style": "string",
        "color_palette": [
            {"name": "string", "hex": "#RRGGBB", "usage": "string"}
        ],
        "shot_list": [
            {
                "shot_number": "int",
                "shot_type": "string (Wide/Medium/Close-up/OTS/POV etc.)",
                "camera_movement": "string",
                "framing": "string",
                "lighting": "string",
                "purpose": "string"
            }
        ],
        "storyboard_prompts": ["string", "string", "string"],
        "writer_notes": {
            "emotional_beat": "string",
            "subtext": "string",
            "dialogue_suggestions": ["string"]
        },
        "confidence": "float 0-1"
    }

    mode_value = "writer" if mode == "writer" else "director"
    req_writer = "Include writer_notes with rich content." if mode_value == "writer" else "Include writer_notes but keep it brief."
    req_shots = "Provide 5 to 8 shots in shot_list." if mode_value == "director" else "Provide 3 to 5 shots in shot_list."

    context_section = ""
    if context_text:
        context_section = f"\n{context_text}\n"

    return f"""
You are SceneSense AI — a cinematic intelligence engine for filmmakers.
Analyze the screenplay scene and return ONLY valid JSON.
No markdown, no code fences, no extra commentary.

Mode: {mode_value}

{context_section}

Required behavior:
- emotion: concise (e.g., tense, intimate, hopeful, eerie)
- narrative_purpose: one strong sentence explaining WHY this scene exists
- visual_mood: lighting + atmosphere in one sentence
- camera_style: movement/framing guidance in one sentence
- genre, tone, intensity(1-10) must be present
- color_palette: MUST be included. Provide exactly 3 cohesive colors with valid HEX codes.
- storyboard_prompts: exactly 3 cinematic prompts (like instructions to a storyboard artist)
- {req_shots}
- The 'shot_list' array is REQUIRED. Each shot must have narrative purpose.
- confidence: 0-1
- {req_writer}

JSON schema (types guidance):
{json.dumps(schema, indent=2)}

Scene:
{scene_text}
""".strip()


def call_qubrid(scene_text: str, mode: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """Call the Qubrid API for Llama 3.3 70B."""
    load_dotenv()
    api_key = os.getenv("QUBRID_API_KEY", "").strip()
    
    if not api_key:
        raise RuntimeError("QUBRID_API_KEY not found. Add it to .env.")

    url = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = build_prompt(scene_text, mode)

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [
            {"role": "system", "content": "You return strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "top_p": 0.9
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            resp_json = response.json()
            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                text = resp_json["choices"][0]["message"]["content"]
            else:
                text = json.dumps(resp_json)
        else:
            text = response.text

    except Exception as e:
        raise RuntimeError(f"Qubrid API call failed: {e}")

    data = extract_json_loose(text)
    if not isinstance(data, dict):
        raise RuntimeError(f"Qubrid Model returned non-JSON. Raw: {text[:200]}...")
    
    if "shot_list" not in data and "shots" in data:
        data["shot_list"] = data["shots"]

    return data


def call_qubrid_with_prompt(prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """Call Qubrid API with a pre-built prompt."""
    load_dotenv()
    api_key = os.getenv("QUBRID_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("QUBRID_API_KEY not found.")
    
    url = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [
            {"role": "system", "content": "You return strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "top_p": 0.9
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    
    try:
        resp_json = response.json()
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            text = resp_json["choices"][0]["message"]["content"]
        else:
            text = json.dumps(resp_json)
    except:
        text = response.text
        
    data = extract_json_loose(text)
    if not isinstance(data, dict):
        raise RuntimeError("Qubrid returned invalid JSON")
    if "shot_list" not in data and "shots" in data:
        data["shot_list"] = data["shots"]
    return data


def analyze_scene(
    scene_text: str, 
    mode: str, 
    model: str, 
    temperature: float = 0.4, 
    max_tokens: int = 1200, 
    context_text: str = ""
) -> Dict[str, Any]:
    """
    Main analysis function that dispatches to the appropriate model.
    """
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found. Add it to .env.")

    if Groq is None:
        raise RuntimeError("groq package not found. Install with: pip install groq")

    prompt = build_prompt(scene_text, mode, context_text)

    if model == "llama-3.3-70b-versatile":
        return call_qubrid_with_prompt(prompt, temperature, max_tokens)

    client = Groq(api_key=api_key)

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": "You return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
    )

    text = resp.choices[0].message.content if resp and resp.choices else ""
    data = extract_json_loose(text)
    if not isinstance(data, dict):
        raise RuntimeError("Model returned non-JSON or invalid JSON. Try again or reduce temperature.")
    return data
