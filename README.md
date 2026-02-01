🎯 What is SceneSense AI?
SceneSense AI is a comprehensive AI-powered cinematic intelligence platform that takes raw screenplay text and transforms it into structured, actionable production intelligence — including emotion detection, shot lists, AI-generated storyboard images, risk assessments, and narrative continuity tracking.
The Problem
In film production, screenplay scenes are unstructured text. Teams spend hours manually discussing:

What is the emotional tone of this scene?
What camera movements and shot types fit this moment?
What are the production risks and feasibility concerns?
How do we maintain visual consistency across scenes?

This process is slow, inconsistent, and expensive.
Our Solution
📝 Screenplay Text → 🤖 AI Analysis → 🎬 Structured Production Intelligence + 🖼️ AI Storyboards
SceneSense AI provides instant, structured cinematic breakdowns with dual-mode analysis (Director & Writer), AI storyboard image generation, production risk assessment, and cross-scene narrative memory — all powered by 100% free APIs.

🏆 Problem Statements Addressed
PBSProblem StatementModuleStatusPBS 2Scene Director Intelligencescene_director.py✅ CompletePBS 3Production Risk Analyzerscene_risk_analyzer.py✅ CompletePBS 1Character Memory & Consistencycharacter_memory.py✅ CompletePBS 4Semantic Footage Searchfootage_search.py✅ CompletePBS 5Best-Take Selection Assistanttake_selection.py✅ Complete

✨ Features
🎬 PBS 2 — Scene Director Intelligence (Primary)
The core engine that analyzes screenplay scenes using Groq LLM (LLaMA 3.1/3.3) and produces comprehensive director-level output.

Emotion & Genre Detection — Identifies dominant emotion (tension, romance, fear, etc.) and genre
Shot List Generation — 5-8 production-ready shots with camera movement, framing, lighting, and purpose
Cinematic Color Palette — 3 cinema-grade colors with HEX codes and usage descriptions
Storyboard Prompts — Detailed text prompts for key visual frames
Dual Mode Analysis:

🎥 Director Mode — Shot lists, camera work, color palettes, visual direction
✍️ Writer Mode — Emotional beats, subtext, dialogue suggestions, narrative purpose


Intensity Scoring — 1-10 scale for pacing guidance
Confidence Rating — 0-1 reliability score per analysis

🖼️ AI Storyboard Generation (Gemini Nano Banana)

Per-shot image generation using Gemini 2.5 Flash Image model
Cinematic prompt builder incorporating shot type, lighting, mood, and color palette
Disk caching with MD5 hash — regenerating the same shot is instant
Smart retry with exponential backoff (15s → 30s → 45s) for rate limits
Free tier: Up to 1,500 images/day from Google AI Studio

⚠️ PBS 3 — Production Risk Analyzer (Primary)
Evaluates every scene for production feasibility from a Line Producer's perspective.

Risk Factor Detection — Stunts, VFX, night shoots, weather, crowds, pyrotechnics, child actors, animal handling
Severity Assessment — Low / Medium / High per risk factor with production-focused reasoning
Mitigation Suggestions — Actionable solutions for each identified risk
Overall Risk Level — Scene-level classification with justification

🧠 Narrative Memory (RAG Engine)

Upload full screenplay (PDF/TXT) to build memory index
FAISS vector store with Sentence Transformer embeddings (all-MiniLM-L6-v2)
Cross-scene context retrieval — AI references earlier scenes when analyzing later ones
Chunked indexing with overlapping windows for comprehensive coverage

🔍 PBS 1 — Character Memory & Consistency

CLIP-based multimodal embeddings for character profiles (text + image)
Cosine similarity matching to ensure consistency across AI-generated images
Character attribute tracking — Physical traits, costume, accessories
Consistency scoring — 0-1 scale per generation

🎞️ PBS 4 — Semantic Footage Search

FAISS vector database for fast similarity search
Sentence Transformer embeddings for semantic understanding
Multi-format support — SRT, VTT, and plain text transcripts
Ranked results with timestamps and relevance scores

🎭 PBS 5 — Best-Take Selection

Whisper speech-to-text for dialogue accuracy scoring
Audio clarity assessment — SNR-based quality levels (Excellent/Good/Fair/Poor)
Emotional alignment scoring against intended scene emotion
Composite weighted scoring with configurable weights

🎥 Director's Full Script Analyzer

Embedded external tool — Full screenplay analysis from director's perspective
Story structure analysis — Save the Cat, Harmon Circle, 3-Act structure
Character arcs, emotional graphs, act breakdowns
VFX/Stunt/Legal breakdowns and art property detection
Accessible via dedicated tab in the app

📁 Batch Processing

Upload complete screenplay (.txt file)
Auto-splits into individual scenes using INT./EXT. markers
Sequential analysis of up to 12 scenes with progress bar
CSV export for spreadsheet analysis and production boards

📥 Export & Download

JSON export — Complete structured analysis data
CSV export — Shot lists and batch results for spreadsheets
Raw JSON viewer — Toggle for developers and debugging


⚙️ Tech Stack
CategoryTechnologyPurposeFrontendStreamlitWeb UI with dark theme & glassmorphismLLM InferenceGroq API (FREE)Scene analysis, risk assessment, shot generationLLM ModelsLLaMA 3.1-8B / 3.3-70BSelectable in sidebar for speed vs qualityImage GenerationGemini Nano Banana (FREE)AI storyboard images per shotImage Modelgemini-2.5-flash-imageGoogle's native image generation modelVector DatabaseFAISSSemantic search & narrative memoryEmbeddingsSentence TransformersText embeddings for RAG & searchSpeech-to-TextWhisper (OpenAI)Dialogue accuracy in take selectionMultimodalCLIPCharacter consistency embeddingsLanguagePython 3.9+All backend modules

💰 Cost: 100% FREE APIs. Groq provides free LLM inference. Gemini provides free image generation (up to 1,500 images/day). No credit card required for any service.


🚀 Installation
Prerequisites

Python 3.9 or higher
Git

Step 1: Clone the Repository
bashgit clone https://github.com/yourusername/scenesense-ai.git
cd scenesense-ai
Step 2: Create Virtual Environment
bash# Create
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
Step 3: Install Dependencies
bashpip install -r requirements.txt
Step 4: Configure API Keys
bash# Copy the example env file
cp .env.example .env
Edit .env and add your keys:
env# Required — Groq (free at console.groq.com)
GROQ_API_KEY=gsk_your_key_here

# Required for storyboard images — Gemini (free at aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIza_your_key_here

# Optional — Qubrid for Llama 3.3 70B
QUBRID_API_KEY=your_key_here
Step 5: Run the Application
bashstreamlit run app.py
Open your browser to: http://localhost:8501

🔑 API Keys (All Free)
APIGet KeyFree TierPurposeGroqconsole.groq.comGenerous free tierLLM inference (scene analysis, risk assessment)Geminiaistudio.google.com/app/apikey~1,500 images/dayAI storyboard image generationQubrid (Optional)platform.qubrid.comLimited freeLlama 3.3 70B access

⚡ No credit card required for Groq or Gemini. Both are instant signup.


📖 Usage
Single Scene Analysis

Launch the app → Click ENTER SCENESENSE AI on the landing page
Select 🎥 Director Mode or ✍️ Writer Mode in the sidebar
Paste your screenplay scene text (or load an example)
Click ⚡ ANALYZE SCENE
Explore results: emotion metrics, shot list, color palette, risk assessment
Open any shot → Click Analyze & Generate Image for AI storyboard
Export results as JSON or CSV

Batch Processing

Switch to the 📁 Batch Processing tab
Upload a .txt screenplay file
Click 🚀 Run Batch Analysis
View results table and download CSV

Director's Full Script Analyzer

Switch to the 🎥 Director's Full Script Analyzer tab
Click the button to open the full script analysis tool
Analyze entire screenplays for story structure, character arcs, and more

Narrative Memory (RAG)

In the sidebar, upload your full screenplay (PDF/TXT)
The system chunks and embeds the content into FAISS
Future analyses will automatically include relevant cross-scene context


📝 Example
Input
INT. ABANDONED WAREHOUSE - NIGHT

The metal door creaks open. Riya steps inside, holding her phone like a torch.
Water drips from the ceiling. Somewhere deep in the dark — a faint CLICK.

She freezes. Her breath turns shallow. A shadow moves behind a pillar.

RIYA: Hello...?

Silence. Then— a slow FOOTSTEP, closer this time.
Output (Director Mode)
FieldOutputEmotionFear / TensionGenreThriller / HorrorIntensity8/10Visual MoodLow-key lighting, deep shadows, cold blue undertonesCamera StyleHandheld close-ups, slow push-in, dutch anglesShots Generated8 shots (Medium, Close-up, Low Angle, POV, Wide, etc.)Color Palette#1A1A2E Deep Navy · #16213E Steel Blue · #E94560 Danger RedRisk LevelMedium (night shoot, confined location, stunt potential)
Each shot includes detailed camera movement, framing, lighting, and purpose — plus click-to-generate AI storyboard images.

🏗️ Architecture
┌──────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI (app.py)                     │
│          Dark Theme · Glassmorphism · 3 Tabs · Sidebar       │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌──────────────────────┐
│    Scene      │  │    Risk       │  │    Narrative          │
│    Director   │  │    Analyzer   │  │    Memory (RAG)       │
│   (PBS 2)     │  │   (PBS 3)     │  │   FAISS + Sentence    │
│    Groq LLM   │  │    Groq LLM   │  │    Transformers       │
└───────┬───────┘  └───────────────┘  └──────────────────────┘
        │
        ▼
┌───────────────┐  ┌───────────────┐  ┌──────────────────────┐
│  Shot Image   │  │  Character    │  │  Footage Search      │
│  Generator    │  │  Memory       │  │  (PBS 4)             │
│  Gemini 🍌    │  │  (PBS 1)      │  │  FAISS Vector DB     │
│  Nano Banana  │  │  CLIP + Cosine│  │                      │
└───────────────┘  └───────────────┘  └──────────────────────┘
                                      ┌──────────────────────┐
                                      │  Best-Take Selection │
                                      │  (PBS 5)             │
                                      │  Whisper + Scoring   │
                                      └──────────────────────┘
File Structure
scenesense-ai/
├── app.py                          # Main Streamlit app (561 lines)
├── requirements.txt                # Python dependencies
├── .env.example                    # API key template
├── .gitignore
├── README.md
├── assets/
│   └── hackfest_banner.jpeg        # Landing page banner
└── ai_modules/
    ├── __init__.py                 # Module exports
    ├── scene_director.py           # PBS 2 — Scene analysis & shot lists (293 lines)
    ├── scene_risk_analyzer.py      # PBS 3 — Risk assessment engine (157 lines)
    ├── narrative_memory.py         # RAG engine — FAISS + embeddings (143 lines)
    └── shot_image_generator.py     # Gemini Nano Banana image gen (325 lines)
Data Flow
User pastes screenplay
        │
        ▼
Groq LLM analyzes scene (PBS 2) ──→ Emotion, genre, intensity, tone
        │                                    │
        ▼                                    ▼
Generates shot list (5-8 shots)       Color palette (3 HEX colors)
        │                                    │
        ▼                                    ▼
User clicks shot ──→ Gemini Nano Banana generates storyboard image
        │
        ▼
Risk Analyzer evaluates (PBS 3) ──→ Risk factors, severity, mitigations
        │
        ▼
Narrative Memory provides cross-scene context via FAISS RAG
        │
        ▼
Results displayed with JSON/CSV export options

🎨 UI/UX Design

Dark gradient background (#0A0E17 → #0F172A) for reduced eye strain
Electric Teal (#00D4AA) primary accent for actions and highlights
Deep Violet (#8B5CF6) secondary accent
Glassmorphism cards with subtle borders and backdrop blur
Native Streamlit landing page with banner image
Responsive layout with sidebar controls and tabbed navigation
Expander-based shot list for clean information hierarchy


🛠️ Configuration
Model Selection
ModelSpeedQualityBest Forllama-3.1-8b-instant⚡ FastGoodQuick iterations, demosllama-3.3-70b-versatile🐢 SlowerBestFinal analysis, production
Sidebar Controls

Analysis Mode — Director / Writer toggle
LLM Model — Speed vs quality selection
Creativity — Temperature slider (0.0 - 1.0)
Max Tokens — Output length control (400 - 2500)
Gemini API Key — For shot image generation
Narrative Memory — PDF/TXT upload for RAG context


📊 Output Schema
json{
  "mode": "director",
  "emotion": "tension",
  "genre": "Thriller",
  "tone": "Suspenseful, Paranoid",
  "intensity": 8,
  "narrative_purpose": "Build anticipation and establish protagonist vulnerability",
  "visual_mood": "Low-key lighting, deep shadows, cold blue undertones",
  "camera_style": "Handheld close-ups, slow push-in, dutch angles",
  "color_palette": [
    { "name": "Midnight Blue", "hex": "#1A237E", "usage": "Primary atmosphere" },
    { "name": "Steel Gray", "hex": "#455A64", "usage": "Industrial surfaces" },
    { "name": "Dim Amber", "hex": "#FF8F00", "usage": "Phone light accent" }
  ],
  "shot_list": [
    {
      "shot_number": 1,
      "shot_type": "Wide",
      "camera_movement": "Slow dolly in",
      "framing": "Full warehouse interior",
      "lighting": "Single phone light source",
      "purpose": "Establish isolation and scale of danger"
    }
  ],
  "storyboard_prompts": [
    "Wide shot of dark warehouse interior, single phone light...",
    "Close-up of Riya's face, fear in her eyes...",
    "Low angle of shadow moving behind concrete pillar..."
  ],
  "writer_notes": {
    "emotional_beat": "Audience should feel dread building",
    "subtext": "Riya knows she's not alone but pushes forward",
    "dialogue_suggestions": ["Who's there?", "I know someone's here."]
  },
  "confidence": 0.87
}

🎯 Use Cases

Pre-Production Planning — Quick alignment on visual direction
Director's Prep — Shot list and mood reference
DP/Cinematographer Collaboration — Lighting and camera guidance
Script Breakdowns — Batch analysis for scheduling
Pitch Decks — Visual mood boards generated from text
Film Schools — Teaching cinematography and production planning concepts
Independent Filmmakers — Professional-grade analysis without expensive tools


⚡ Rate Limits & Tips
ServiceFree Tier LimitTipGroq~30 requests/minuteMore than enough for scene analysisGemini Images~5-15 requests/minuteGenerate one shot, wait 60-90s, generate nextGemini Daily~1,500 images/dayCached images are instant (no API call)

Images are cached by MD5 hash — clicking the same shot twice is instant
If rate limited, the app retries automatically (15s → 30s → 45s)
Use LLaMA 3.1-8B for faster iterations, 3.3-70B for final quality
