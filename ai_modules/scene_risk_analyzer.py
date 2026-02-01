"""
Scene Risk Analyzer Module for SceneSense AI
Production feasibility and risk assessment engine
"""

import json
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()

RISK_MODEL = "llama-3.1-8b-instant"


def extract_json_safe(text: str) -> Dict[str, Any]:
    """Safely extract JSON from LLM output."""
    if not text:
        return {}
    
    text = text.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(text)
    except:
        pass
    
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    return {}


def analyze_scene_risk(scene_text: str) -> Dict[str, Any]:
    """
    Analyze a scene for production risks and feasibility.
    Returns structured risk assessment data.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    if not api_key:
        return {
            "overall_risk_level": "Unknown",
            "detected_risks": [],
            "justification": "GROQ_API_KEY not found",
            "mitigation_suggestions": [],
            "confidence": 0.0
        }
    
    if Groq is None:
        return {
            "overall_risk_level": "Unknown",
            "detected_risks": [],
            "justification": "groq package not installed",
            "mitigation_suggestions": [],
            "confidence": 0.0
        }

    client = Groq(api_key=api_key)

    prompt = f"""
You are a film production safety and feasibility expert.
Think like a Line Producer, not a generic safety checklist.

Analyze the following script scene from a PRODUCTION perspective.
Use reasoning, not keyword matching.

Identify risks related to:
- Crowd management (extras, public locations)
- Night shoots (lighting, safety, crew fatigue)
- Weather dependency (rain, snow, wind, outdoor conditions)
- Physical stunts (action, falls, fights, vehicles)
- Visual effects complexity (VFX shots, CGI requirements)
- Location logistics (remote areas, permits, access)
- Equipment needs (specialized cameras, rigs, cranes)

For each detected risk:
- Explain WHY it is risky from a production standpoint
- Assess severity realistically (Low/Medium/High)
- Consider budget and scheduling implications

Then provide:
- Overall risk level: Low / Medium / High
- Clear justification based on production realities
- Practical, actionable mitigation strategies

Return ONLY valid JSON. No markdown. No extra commentary.

JSON format:
{{
  "overall_risk_level": "Low/Medium/High",
  "detected_risks": [
    {{
      "factor": "Risk Factor Name",
      "severity": "Low/Medium/High",
      "reason": "Clear production-focused explanation"
    }}
  ],
  "justification": "Overall production reasoning",
  "mitigation_suggestions": ["Practical suggestion 1", "Practical suggestion 2"],
  "confidence": 0.0
}}

Scene:
\"\"\"{scene_text}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=RISK_MODEL,
            messages=[
                {"role": "system", "content": "You are a film production expert. Return strict JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        result = extract_json_safe(content)
        
        if not result:
            return {
                "overall_risk_level": "Unknown",
                "detected_risks": [],
                "justification": "Could not parse risk analysis response",
                "mitigation_suggestions": [],
                "confidence": 0.0
            }
        
        # Ensure all required fields exist
        result.setdefault("overall_risk_level", "Unknown")
        result.setdefault("detected_risks", [])
        result.setdefault("justification", "")
        result.setdefault("mitigation_suggestions", [])
        result.setdefault("confidence", 0.75)
        
        return result
        
    except Exception as e:
        return {
            "overall_risk_level": "Unknown",
            "detected_risks": [],
            "justification": f"Error analyzing risk: {str(e)}",
            "mitigation_suggestions": [],
            "confidence": 0.0
        }
