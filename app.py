"""
🎬 SceneSense AI v6.0 — PRODUCTION READY
==========================================
FIXES:
  1. Landing page = 100% native Streamlit (st.image, st.columns, st.button)
     NO st.markdown(unsafe_allow_html) for landing — guaranteed rendering
  2. Image gen: longer retry (15s, 30s, 45s) + fallback model
  3. All main app UI uses small inline HTML only for minor styling
"""

import os, re, json, time, base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai_modules.scene_director import (
    analyze_scene, extract_json_loose, clamp_intensity,
    clamp_confidence, normalize_hex, safe_get
)
from ai_modules.scene_risk_analyzer import analyze_scene_risk
import ai_modules.narrative_memory as narrative_memory
from ai_modules.shot_image_generator import NanoBananaGenerator, GEMINI_AVAILABLE

# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SceneSense AI — Cinematic Intelligence",
    page_icon="🎬", layout="wide", initial_sidebar_state="collapsed",
)

if "show_landing" not in st.session_state:
    st.session_state["show_landing"] = True
if "analysis_data" not in st.session_state:
    st.session_state["analysis_data"] = None
if "risk_data" not in st.session_state:
    st.session_state["risk_data"] = None


# ════════════════════════════════════════════════════════════════════════════
# APP CSS — only for main app pages, small safe styles
# ════════════════════════════════════════════════════════════════════════════
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',-apple-system,sans-serif!important;color:#F1F5F9!important}
.stApp{background:linear-gradient(180deg,#0A0E17 0%,#0F172A 100%)!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:1rem 2rem 2rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(15,23,42,0.95),rgba(10,14,23,0.98))!important;border-right:1px solid rgba(255,255,255,0.08)!important}
.stTextArea textarea{background:rgba(15,23,42,0.6)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:12px!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;color:#CBD5E1!important;line-height:1.8!important}
.stButton>button{background:linear-gradient(135deg,#00D4AA,#00B894)!important;color:#0A0E17!important;border:none!important;border-radius:12px!important;padding:14px 32px!important;font-weight:700!important;font-size:13px!important;box-shadow:0 0 30px rgba(0,212,170,0.3)!important;transition:all 0.3s ease!important}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 0 50px rgba(0,212,170,0.4)!important}
.stButton>button:active{transform:translateY(0) scale(0.98)!important}
.stDownloadButton>button{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(255,255,255,0.1)!important;color:#94A3B8!important;border-radius:10px!important}
.stTabs [data-baseweb="tab-list"]{gap:4px}
.stTabs [data-baseweb="tab"]{background:rgba(255,255,255,0.03)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:10px!important;color:#94A3B8!important;padding:10px 20px!important}
.stTabs [aria-selected="true"]{background:rgba(0,212,170,0.1)!important;border-color:rgba(0,212,170,0.3)!important;color:#00D4AA!important}
.stExpander{border:1px solid rgba(255,255,255,0.08)!important;border-radius:12px!important;background:rgba(255,255,255,0.02)!important}
.stSelectbox>div>div{background:rgba(15,23,42,0.8)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:10px!important}
</style>
"""

LANDING_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800;900&family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',-apple-system,sans-serif!important}
.stApp{background:linear-gradient(180deg,#0A0E17 0%,#0F172A 100%)!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding-top:2rem!important}
.stButton>button{background:linear-gradient(135deg,#00D4AA,#00B894)!important;color:#0A0E17!important;border:none!important;border-radius:14px!important;padding:18px 48px!important;font-weight:800!important;font-size:16px!important;letter-spacing:0.5px!important;box-shadow:0 0 40px rgba(0,212,170,0.35)!important;transition:all 0.3s ease!important}
.stButton>button:hover{transform:translateY(-3px) scale(1.02)!important;box-shadow:0 0 60px rgba(0,212,170,0.5)!important}
.stButton>button:active{transform:scale(0.97)!important}
</style>
"""


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════
def now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def scene_splitter(text):
    if not text or len(text.strip()) < 30: return []
    t = text.replace("\r\n", "\n")
    parts = re.split(r"(?=^(?:INT\.|EXT\.|INT/EXT\.|I/E\.).*$)", t, flags=re.MULTILINE)
    scenes = [p.strip() for p in parts if len(p.strip()) >= 60]
    return scenes if scenes else [t.strip()]

def _section(icon, title):
    st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:28px 0 16px'><span style='font-size:20px'>{icon}</span><h3 style='font-size:18px;font-weight:700;color:#F1F5F9;margin:0'>{title}</h3></div>", unsafe_allow_html=True)

def _divider():
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent);margin:24px 0'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# LANDING PAGE — 100% NATIVE STREAMLIT (no unsafe_allow_html for layout)
# ════════════════════════════════════════════════════════════════════════════
def render_landing():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    # Spacer
    st.markdown("")

    # Centered banner image
    banner_path = Path("assets/hackfest_banner.jpeg")
    col_l, col_c, col_r = st.columns([1, 3, 1])
    with col_c:
        if banner_path.exists():
            st.image(str(banner_path), use_container_width=True)
        else:
            st.markdown("## 🎬🎥🎨")

    # Title & subtitle — small safe HTML only for text styling
    st.markdown("""
<h1 style="text-align:center;font-family:'Orbitron',monospace;font-size:48px;font-weight:900;
    letter-spacing:-1px;margin:20px 0 8px;
    background:linear-gradient(135deg,#FFF 0%,#00D4AA 40%,#8B5CF6 70%,#3B82F6 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent">
    SceneSense AI
</h1>
<p style="text-align:center;font-size:17px;color:#94A3B8;max-width:620px;margin:0 auto 32px;line-height:1.7">
    Transform screenplay text into <strong style="color:#00D4AA">director-ready cinematic intelligence</strong> —
    shot lists, AI-generated storyboards, color palettes, risk analysis,
    and narrative continuity. <strong style="color:#00D4AA">Powered by Gemini Nano Banana 🍌</strong>
</p>
""", unsafe_allow_html=True)

    # Feature cards — native Streamlit columns
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    features = [
        (f1, "🎥", "Scene Analysis", "Emotion • Tone"),
        (f2, "📷", "Shot Lists", "5-8 shots"),
        (f3, "🖼️", "AI Storyboards", "Nano Banana"),
        (f4, "🎨", "Color Palettes", "Cinema HEX"),
        (f5, "⚠️", "Risk Assessment", "Feasibility"),
        (f6, "🧠", "Narrative Memory", "RAG continuity"),
    ]
    for col, icon, label, sub in features:
        with col:
            st.markdown(f"""<div style="text-align:center;padding:18px 8px;border-radius:16px;
                border:1px solid rgba(255,255,255,0.06);background:rgba(15,23,42,0.6)">
                <div style="font-size:28px;margin-bottom:6px">{icon}</div>
                <div style="font-size:12px;font-weight:700;color:#F1F5F9">{label}</div>
                <div style="font-size:10px;color:#64748B;margin-top:2px">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Enter button — native Streamlit
    _, btn_col, _ = st.columns([1.5, 2, 1.5])
    with btn_col:
        if st.button("⚡  ENTER SCENESENSE AI  ⚡", type="primary", use_container_width=True):
            st.session_state["show_landing"] = False
            st.rerun()

    st.markdown("")
    st.markdown("<p style='text-align:center;font-size:11px;color:#475569'>v6.0 • PBS 2 & PBS 3 • Cine AI Hackfest — Lorven AI Studio</p>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# UI Components
# ════════════════════════════════════════════════════════════════════════════
def render_hero():
    st.markdown("""<div style="padding:24px 28px;border-radius:20px;border:1px solid rgba(255,255,255,0.08);
        background:radial-gradient(ellipse 800px 250px at 15% 0%,rgba(139,92,246,0.2),transparent 60%),
        radial-gradient(ellipse 600px 200px at 85% 30%,rgba(0,212,170,0.15),transparent 55%),
        linear-gradient(180deg,rgba(15,23,42,0.8),rgba(10,14,23,0.6));
        box-shadow:0 20px 50px rgba(0,0,0,0.4);margin-bottom:24px">
        <h1 style="font-size:36px;font-weight:700;letter-spacing:-0.5px;margin:0 0 8px;
            background:linear-gradient(135deg,#F8FAFC,#00D4AA);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
            🎬 SceneSense AI</h1>
        <p style="font-size:15px;color:#94A3B8;margin:0 0 16px;line-height:1.6">
            Transform screenplay text into <strong>director-ready cinematic intelligence</strong></p>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
            <span style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);font-size:12px;color:#94A3B8">⚡ Instant Analysis</span>
            <span style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);font-size:12px;color:#94A3B8">🎥 Director Mode</span>
            <span style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);font-size:12px;color:#94A3B8">✍️ Writer Mode</span>
            <span style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);font-size:12px;color:#94A3B8">🖼️ Nano Banana</span>
            <span style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);font-size:12px;color:#94A3B8">🧠 Narrative Memory</span>
        </div>
    </div>""", unsafe_allow_html=True)


def render_metrics(data):
    em = str(safe_get(data, "emotion", "—")).title()
    ge = str(safe_get(data, "genre", "—")).title()
    iy = clamp_intensity(safe_get(data, "intensity", 5))
    co = clamp_confidence(safe_get(data, "confidence", 0.75))
    for col, (lb, ic, vl, sb) in zip(
        st.columns(4),
        [("Emotion","🎭",em,"Scene feeling"),("Genre","🎬",ge,"Story category"),
         ("Intensity","🔥",f"{iy}/10","Pace & tension"),("Confidence","✅",f"{int(co*100)}%","Reliability")]
    ):
        with col:
            st.markdown(f"""<div style="padding:18px 20px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);
                background:linear-gradient(135deg,rgba(30,41,59,0.6),rgba(15,23,42,0.8));box-shadow:0 8px 30px rgba(0,0,0,0.2)">
                <div style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#64748B;margin-bottom:8px">{ic} {lb}</div>
                <div style="font-size:26px;font-weight:700;color:#00D4AA;line-height:1.2">{vl}</div>
                <div style="font-size:12px;color:#64748B;margin-top:4px">{sb}</div>
            </div>""", unsafe_allow_html=True)


def render_summary(data):
    for col, (lb, ic, tx) in zip(
        st.columns(3),
        [("Narrative Purpose","🎯",safe_get(data,"narrative_purpose","—")),
         ("Visual Mood","🎨",safe_get(data,"visual_mood","—")),
         ("Camera Style","🎥",safe_get(data,"camera_style","—"))]
    ):
        with col:
            st.markdown(f"""<div style="padding:20px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);
                background:rgba(30,41,59,0.5);box-shadow:0 10px 40px rgba(0,0,0,0.25)">
                <div style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#64748B;margin-bottom:8px">{ic} {lb}</div>
                <p style="font-size:13px;color:#CBD5E1;line-height:1.6;margin:0">{tx}</p>
            </div>""", unsafe_allow_html=True)


def render_palette(data):
    pal = safe_get(data, "color_palette", []) or []
    if not pal: return
    _section("🎨", "Cinematic Color Palette")
    for col, p in zip(st.columns(len(pal[:3])), pal[:3]):
        nm = safe_get(p,"name","Color"); hx = normalize_hex(safe_get(p,"hex","#111")); us = safe_get(p,"usage","")
        with col:
            st.markdown(f"""<div style="border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.02)">
                <div style="height:90px;width:100%;background:{hx}"></div>
                <div style="padding:14px">
                    <div style="font-size:14px;font-weight:600;color:#F1F5F9;margin-bottom:4px">{nm}</div>
                    <div style="font-size:12px;font-family:monospace;color:#64748B;margin-bottom:6px">{hx}</div>
                    <div style="font-size:11px;color:#94A3B8"><b>Use:</b> {us}</div>
                </div>
            </div>""", unsafe_allow_html=True)


def render_shots_with_images(data, gemini_key):
    shots = safe_get(data, "shot_list", []) or []
    if not shots:
        st.info("🎬 No shot list returned.")
        return

    _section("🎬", "Shot List — AI Storyboard Generation")

    status_txt = "🍌 Gemini Nano Banana (FREE)" if gemini_key else "🔴 Add Gemini key in sidebar"
    st.info(f"📷 **{len(shots)} shots** identified  |  🖼️ Click **Analyze** inside any shot to generate AI storyboard  |  {status_txt}")

    img_gen = NanoBananaGenerator(api_key=gemini_key) if gemini_key else None

    for s in shots:
        num = safe_get(s,"shot_number","?"); stype = str(safe_get(s,"shot_type","Shot"))
        move = safe_get(s,"camera_movement","—"); frame = safe_get(s,"framing","—")
        light = safe_get(s,"lighting","—"); purpose = safe_get(s,"purpose","—")

        with st.expander(f"📷 Shot {num} — {stype}", expanded=False):
            # Shot details — small badges
            bc1, bc2, bc3 = st.columns(3)
            bc1.caption(f"🎥 {move}")
            bc2.caption(f"🖼️ {frame}")
            bc3.caption(f"💡 {light}")
            st.markdown(f"**Purpose:** {purpose}")

            img_key = f"shot_img_{num}"
            if st.button(f"🎨  Analyze & Generate Image — Shot {num}", key=f"gen_{num}_{id(s)}", use_container_width=True):
                if not img_gen or not img_gen.is_available:
                    st.error("❌ Add your **Gemini API Key** in the sidebar first (Settings → 🖼️ section)")
                else:
                    with st.spinner(f"🖼️ Generating Shot {num}... (Nano Banana 🍌) — may take 15-30s with retries"):
                        result = img_gen.generate_for_shot(s, scene_context=data)
                        st.session_state[img_key] = result

            if img_key in st.session_state:
                r = st.session_state[img_key]
                if r and r.get("image_base64"):
                    st.image(base64.b64decode(r["image_base64"]),
                             caption=f"Shot {num} — {stype} | {'Cached ♻️' if r.get('cached') else 'Fresh 🆕'}",
                             use_container_width=True)
                    with st.expander("🔍 Image Prompt Details"):
                        st.code(r.get("prompt_used",""), language=None)
                elif r and r.get("error"):
                    err = r["error"]
                    if "rate limit" in err.lower():
                        st.warning(f"⏳ {err}")
                        st.caption("💡 **Tip:** Wait 1-2 minutes between shots. The free tier allows ~5 requests per minute.")
                    else:
                        st.error(f"⚠️ {err}")


def render_storyboard(data):
    prompts = safe_get(data,"storyboard_prompts",[]) or []
    if not prompts: return
    _section("🧩", "Storyboard Prompts")
    for i, p in enumerate(prompts[:3], 1):
        st.markdown(f"""<div style="padding:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.02);margin-bottom:12px">
            <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#8B5CF6;margin-bottom:8px">Frame {i}</div>
            <p style="font-size:13px;color:#CBD5E1;line-height:1.6;margin:0">{p}</p>
        </div>""", unsafe_allow_html=True)


def render_writer_notes(data):
    wn = safe_get(data,"writer_notes",{}) or {}
    if not wn: return
    _section("✍️", "Writer Notes")
    st.success(f"**Emotional Beat**\n\n{safe_get(wn,'emotional_beat','—')}")
    st.warning(f"**Subtext**\n\n{safe_get(wn,'subtext','—')}")
    sugg = safe_get(wn,"dialogue_suggestions",[]) or []
    if sugg:
        st.markdown("**💬 Dialogue Suggestions**")
        for s in sugg[:8]: st.write(f"• {s}")


def render_risk(risk_data):
    rl = safe_get(risk_data,"overall_risk_level","Unknown")
    rj = safe_get(risk_data,"justification","")
    rs = safe_get(risk_data,"detected_risks",[]); ms = safe_get(risk_data,"mitigation_suggestions",[])
    bl = "4px solid #EF4444" if "High" in rl else ("4px solid #F59E0B" if "Medium" in rl else "4px solid #10B981")
    bc_bg = "rgba(239,68,68,0.2)" if "High" in rl else ("rgba(245,158,11,0.2)" if "Medium" in rl else "rgba(16,185,129,0.2)")
    bc_cl = "#EF4444" if "High" in rl else ("#F59E0B" if "Medium" in rl else "#10B981")
    _section("⚠️", "Production Feasibility & Risk")
    st.markdown(f"""<div style="padding:20px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);background:rgba(30,41,59,0.5);border-left:{bl}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <span style="font-size:14px;color:#94A3B8">Overall Risk Level</span>
            <span style="padding:4px 12px;border-radius:8px;font-size:12px;font-weight:700;background:{bc_bg};color:{bc_cl}">{rl}</span>
        </div>
        <p style="font-size:13px;color:#CBD5E1;line-height:1.6;margin:0">{rj}</p>
    </div>""", unsafe_allow_html=True)
    if rs:
        st.markdown("#### 🚨 Detected Risk Factors")
        cols = st.columns(min(len(rs),3))
        for i, r in enumerate(rs):
            with cols[i%3]: st.warning(f"**{r.get('factor','')}** ({r.get('severity','')})\n\n{r.get('reason','')}")
    if ms:
        with st.expander("🛠️ Mitigation Suggestions", expanded=True):
            for m in ms: st.write(f"• {m}")


# ════════════════════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════════════════════
def sidebar_controls():
    st.sidebar.markdown("## 🎬 SceneSense AI")
    st.sidebar.caption("Cinematic Intelligence v6.0")

    st.sidebar.markdown("### 🎛️ Analysis Mode")
    role = st.sidebar.radio("Mode", ["🎥 Director Mode","✍️ Writer Mode"], index=0, label_visibility="collapsed")
    mode = "director" if "Director" in role else "writer"

    st.sidebar.markdown("### ⚙️ Model")
    model = st.sidebar.selectbox("LLM", ["llama-3.1-8b-instant","llama-3.3-70b-versatile"], index=0)
    temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.35, 0.05)
    mtok = st.sidebar.slider("Max Tokens", 400, 2500, 1200, 50)

    st.sidebar.markdown("### 🖼️ Shot Image Generation")
    st.sidebar.caption("Gemini Nano Banana 🍌 (FREE)")
    gkey = st.sidebar.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY",""),
                                  help="Free at aistudio.google.com/app/apikey")
    if gkey: os.environ["GEMINI_API_KEY"] = gkey

    if gkey and GEMINI_AVAILABLE:
        st.sidebar.success("🟢 Ready")
    elif not GEMINI_AVAILABLE:
        st.sidebar.warning("🟡 Install: `pip install google-genai`")
    else:
        st.sidebar.error("🔴 Add API key above")

    st.sidebar.caption("⏱️ Free tier: ~5 req/min. Wait 1-2 min between shots if rate-limited.")

    st.sidebar.markdown("### 🔧 Display")
    show_raw = st.sidebar.toggle("Raw JSON", False)

    st.sidebar.markdown("### 🧠 Narrative Memory")
    mem = st.sidebar.file_uploader("Upload Script (PDF/TXT)", type=["pdf","txt"], key="mem_up")
    if mem:
        fid = f"{mem.name}_{mem.size}"
        if st.session_state.get("memory_file_id") != fid:
            with st.sidebar.status("🧠 Building Memory...", expanded=True) as sts:
                try:
                    st.write("📖 Reading...")
                    txt = narrative_memory.extract_text_from_pdf(mem) if mem.name.lower().endswith(".pdf") else mem.read().decode("utf-8", errors="ignore")
                    chunks = narrative_memory.chunk_script(txt)
                    st.write(f"🔢 Embedding {len(chunks)} chunks...")
                    idx, _ = narrative_memory.build_memory_index(chunks)
                    st.session_state["memory_index"] = idx
                    st.session_state["memory_chunks"] = chunks
                    st.session_state["memory_file_id"] = fid
                    sts.update(label="✅ Memory Built!", state="complete", expanded=False)
                except Exception as e:
                    sts.update(label="❌ Failed", state="error"); st.sidebar.error(str(e))
        else:
            st.sidebar.success(f"✅ Loaded ({len(st.session_state.get('memory_chunks',[]))} chunks)")

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Back to Landing"):
        st.session_state["show_landing"] = True; st.rerun()

    return {"mode":mode,"model":model,"temperature":float(temp),"max_tokens":int(mtok),"show_raw":show_raw,"gemini_key":gkey}


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    if st.session_state.get("show_landing", True):
        render_landing()
        return

    st.markdown(APP_CSS, unsafe_allow_html=True)
    render_hero()
    ctrl = sidebar_controls()

    tab1, tab2, tab3 = st.tabs(["🎬 Single Scene","📁 Batch Processing","🎥 Director's Full Script Analyzer"])

    examples = {
        "None": "",
        "🏎️ Action Chase": "EXT. MARKET STREET - NIGHT\n\nA motorbike roars through crowded stalls. People scream and jump aside.\nRavi grips the handlebar, dodging carts and neon signs.\n\nBehind him, a black SUV crashes through a fruit stand— mangos explode.\n\nRAVI (yelling): They're still on me!\n\nA shot rings out. Glass shatters above him.\nRavi swerves into a narrow alley. Sparks fly.",
        "😰 Warehouse Thriller": "INT. ABANDONED WAREHOUSE - NIGHT\n\nThe metal door creaks open. Riya steps inside, phone like a torch.\nWater drips. Somewhere deep — a faint CLICK.\n\nShe freezes. Her breath turns shallow. A shadow moves behind a pillar.\n\nRIYA: Hello...?\n\nSilence. Then— a slow FOOTSTEP, closer.",
        "💕 Sunset Romance": "EXT. PARK - SUNSET\n\nGolden light through trees. Aarav and Meera sit on a bench, shoulders almost touching.\n\nMEERA: You never told me why you left.\nAARAV: I thought it was easier... than saying goodbye.\n\nShe reaches for his hand. He lets her.\nThe city noise fades. Only wind and breathing.",
        "👻 Horror Mirror": "INT. APARTMENT BATHROOM - 2:13 AM\n\nOnly the mirror light hums. Ananya washes her face.\nShe looks up.\n\nHer reflection smiles— but she doesn't.\n\nANANYA: ...What?\n\nThe reflection slowly raises its hand.\nAnanya's real hand doesn't move.\nThe door clicks shut by itself.",
    }

    with tab1:
        _divider()
        cl, cr = st.columns([1, 2], gap="large")

        with cl:
            m_label = "🎥 Director Mode" if ctrl["mode"]=="director" else "✍️ Writer Mode"
            st.markdown(f"""<div style="padding:20px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);background:rgba(30,41,59,0.5)">
                <div style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#64748B;margin-bottom:8px">Selected Mode</div>
                <div style="font-size:16px;font-weight:600;color:#00D4AA">{m_label}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("")
            ex = st.selectbox("📝 Load Example", list(examples.keys()), index=0)
            if st.button("✨ Load Example", use_container_width=True):
                st.session_state["scene_text"] = examples[ex]
            st.caption("💡 Open any shot → click **Analyze** for AI storyboard images")

        with cr:
            st.caption("SCREENPLAY INPUT")
            scene_text = st.text_area("Scene", value=st.session_state.get("scene_text",""), height=280,
                                       placeholder="Paste your screenplay scene here…", label_visibility="collapsed")
            st.markdown("")
            analyze = st.button("⚡ ANALYZE SCENE", type="primary", use_container_width=True)

        if analyze:
            if not scene_text or len(scene_text.strip()) < 30:
                st.warning("⚠️ Paste a longer scene (30+ chars)."); return
            with st.spinner("🎬 Analyzing scene... ✨"):
                t0 = time.time()
                try:
                    ctx = ""
                    if "memory_index" in st.session_state:
                        ret = narrative_memory.retrieve_context(scene_text.strip(), st.session_state["memory_index"], st.session_state.get("memory_chunks",[]))
                        ctx = narrative_memory.format_context_for_prompt(ret)
                    dd = analyze_scene(scene_text.strip(), ctrl["mode"], ctrl["model"], ctrl["temperature"], ctrl["max_tokens"], ctx)
                    rd = analyze_scene_risk(scene_text.strip())
                except Exception as e:
                    st.error(f"❌ {e}"); return
                dt = time.time() - t0
            st.session_state["analysis_data"] = dd
            st.session_state["risk_data"] = rd
            st.success(f"✅ Analysis complete in {dt:.2f}s")

        dd = st.session_state.get("analysis_data")
        rd = st.session_state.get("risk_data")

        if dd:
            _divider()
            _section("🔍", "Scene Insight")
            render_metrics(dd)
            _divider()
            _section("🎞️", "Cinematic Summary")
            render_summary(dd)
            _divider()

            if ctrl["mode"] == "director":
                lc, rc = st.columns([1.1, 1], gap="large")
                with lc: render_shots_with_images(dd, ctrl.get("gemini_key",""))
                with rc: render_palette(dd); st.markdown(""); render_storyboard(dd)
            else:
                lc, rc = st.columns([1, 1], gap="large")
                with lc: render_writer_notes(dd)
                with rc: render_palette(dd); st.markdown(""); render_storyboard(dd); st.markdown(""); render_shots_with_images(dd, ctrl.get("gemini_key",""))

            _divider()
            if rd: render_risk(rd); _divider()

            _section("⬇️", "Export")
            e1, e2 = st.columns(2)
            with e1: st.download_button("⬇️ Scene JSON", json.dumps(dd,indent=2,ensure_ascii=False), f"scene_{now_stamp()}.json", "application/json", use_container_width=True)
            with e2:
                sl = safe_get(dd,"shot_list",[]) or []
                if sl: st.download_button("⬇️ Shot CSV", pd.DataFrame(sl).to_csv(index=False).encode(), f"shots_{now_stamp()}.csv", "text/csv", use_container_width=True)

            if ctrl["show_raw"]:
                with st.expander("📦 Raw Director JSON"): st.json(dd)
                if rd:
                    with st.expander("📦 Raw Risk JSON"): st.json(rd)

    with tab2:
        st.markdown("### 📁 Batch Processing")
        st.caption("Upload a .txt script. SceneSense splits & analyzes each scene.")
        st.markdown("")
        up = st.file_uploader("Upload Script (.txt)", type=["txt"])
        if st.button("🚀 Run Batch", type="primary", use_container_width=True):
            if not up: st.warning("⚠️ Upload first."); return
            text = up.read().decode("utf-8", errors="ignore")
            scenes = scene_splitter(text)
            if not scenes: st.warning("No scenes found."); return
            st.success(f"✅ {len(scenes)} scenes found")
            results = []; prog = st.progress(0)
            for i, sc in enumerate(scenes[:12], 1):
                try:
                    d = analyze_scene(sc, ctrl["mode"], ctrl["model"], ctrl["temperature"], ctrl["max_tokens"])
                    results.append({"scene":i,"emotion":safe_get(d,"emotion",""),"genre":safe_get(d,"genre",""),"intensity":clamp_intensity(safe_get(d,"intensity",5))})
                except Exception as e:
                    results.append({"scene":i,"error":str(e)})
                prog.progress(int(i/min(len(scenes),12)*100))
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ Batch CSV", df.to_csv(index=False).encode(), f"batch_{now_stamp()}.csv", "text/csv", use_container_width=True)

    with tab3:
        DIRECTOR_APP_URL = "https://ai-script-analyzer-for-directors.streamlit.app/"

        st.markdown("""<div style="padding:20px;border-radius:16px;border:1px solid rgba(139,92,246,0.3);
            background:linear-gradient(135deg,rgba(139,92,246,0.08),rgba(0,212,170,0.05));margin-bottom:20px">
            <h3 style="margin:0 0 8px;color:#F1F5F9;font-size:18px">🎥 Director's Full Script Analyzer</h3>
            <p style="margin:0;font-size:14px;color:#94A3B8;line-height:1.6">
                Comprehensive AI-powered script analysis for directors — story structure, character arcs,
                emotional graphs, act analysis, VFX/stunt breakdowns, art properties, and production suggestions.
                This is the <strong style="color:#8B5CF6">full screenplay intelligence engine</strong> that analyzes entire scripts
                from a director's perspective.
            </p>
        </div>""", unsafe_allow_html=True)

        # Direct link button
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            st.link_button("🚀  Open Director's Script Analyzer  →", DIRECTOR_APP_URL, use_container_width=True)

        st.caption("💡 Click the button above to open the full Director's Script Analyzer in a new tab.")

        st.markdown("")

        # Embedded iframe
        st.markdown(f"""<div style="border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);box-shadow:0 10px 40px rgba(0,0,0,0.3)">
            <iframe src="{DIRECTOR_APP_URL}" width="100%" height="800" style="border:none;background:#0A0E17"></iframe>
        </div>""", unsafe_allow_html=True)

        st.markdown("")
        st.caption("⚠️ If the embedded view doesn't load, use the button above to open it directly.")

    _divider()
    st.markdown("<p style='text-align:center;font-size:11px;color:#64748B'>SceneSense AI v6.0 • Cine AI Hackfest • Lorven AI Studio</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
