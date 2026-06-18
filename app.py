import streamlit as st
import json
import re
import io
from openai import OpenAI

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="PitchScan — VC-Grade Pitch Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Novus.ai analytics injection ───────────────────────────────────────────
NOVUS_APP_ID = "26e1d6da-25ad-4964-981b-411e2faef7b0"
st.markdown(
    f"""
    <script>
      (function(n,o,v,u,s,ai){{
        if(n[s])return;
        n[s]=Object.assign(n[s]||{{}},{{initialize:function(opts){{n[s].q=(n[s].q||[]).concat([["initialize",opts]]);}},identify:function(id,opts){{n[s].q=(n[s].q||[]).concat([["identify",id,opts]]);}},updateOptions:function(opts){{n[s].q=(n[s].q||[]).concat([["updateOptions",opts]]);}},pageLoad:function(){{n[s].q=(n[s].q||[]).concat([["pageLoad"]]);}}}} );
        n[s].initialize({{apiKey:"{NOVUS_APP_ID}"}});
        ai=o.createElement('script');ai.async=true;
        ai.src='https://cdn.novus.pendo.io/agent/static/{NOVUS_APP_ID}/novus.js';
        o.head.appendChild(ai);
      }})(window,document,'novus','novus','novus');
      window.novus.pageLoad();
    </script>
    """,
    unsafe_allow_html=True,
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: #03070f; color: #e2e8f0; }
section[data-testid="stSidebar"] { background: #0a0f1a; }

/* Hide default Streamlit header & footer */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }

/* Main content area */
.block-container { max-width: 960px; padding: 2rem 1rem; }

/* ── Score gauge card ── */
.score-card {
    background: rgba(37,99,235,0.08);
    border: 1px solid rgba(37,99,235,0.4);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    backdrop-filter: blur(10px);
}
.score-number {
    font-size: 5rem;
    font-weight: 700;
    line-height: 1;
    background: linear-gradient(135deg, #C9A84C, #f0d080);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Fira Code', monospace;
}
.score-label { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; margin-top: 0.5rem; }
.verdict-badge {
    display: inline-block;
    padding: 0.4rem 1.4rem;
    border-radius: 99px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 1rem;
    letter-spacing: 1px;
}
.verdict-INVEST  { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid #10b981; }
.verdict-MONITOR { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid #f59e0b; }
.verdict-PASS    { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid #ef4444; }

/* ── Section score bars ── */
.section-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.7rem;
}
.section-name { min-width: 120px; font-size: 0.85rem; color: #94a3b8; text-transform: capitalize; }
.bar-bg {
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 99px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.8s ease;
}
.section-score { min-width: 36px; text-align: right; font-size: 0.85rem; font-family: 'Fira Code', monospace; color: #e2e8f0; }

/* ── Flag / suggestion cards ── */
.flag-card {
    background: rgba(239,68,68,0.06);
    border-left: 3px solid #ef4444;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #fca5a5;
}
.suggestion-card {
    background: rgba(16,185,129,0.06);
    border-left: 3px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #6ee7b7;
}
.comparable-card {
    background: rgba(201,168,76,0.06);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}
.comparable-name { color: #C9A84C; font-weight: 600; }
.comparable-desc { color: #94a3b8; margin-top: 0.2rem; }

/* ── Section headings ── */
.ps-section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 1.8rem 0 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ── Upload zone ── */
.upload-hint { color: #64748b; font-size: 0.85rem; text-align: center; margin-top: 0.5rem; }

/* ── Hero ── */
.hero { text-align: center; padding: 3rem 1rem 2rem; }
.hero h1 { font-size: 2.8rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
.hero h1 span { background: linear-gradient(135deg, #C9A84C, #f0d080); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { color: #64748b; font-size: 1.05rem; max-width: 540px; margin: 0 auto; }

/* ── Progress bar override ── */
div[data-testid="stProgress"] > div { background: linear-gradient(90deg, #2563EB, #C9A84C) !important; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── stMarkdown links ── */
a { color: #C9A84C !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border: 1.5px dashed rgba(201,168,76,0.35) !important;
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(201,168,76,0.7) !important; }

/* ── Buttons ── */
button[kind="primary"], .stButton > button {
    background: linear-gradient(135deg, #2563EB, #1d4ed8) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-weight: 600 !important;
    padding: 0.55rem 2rem !important;
}
button[kind="primary"]:hover, .stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 0 20px rgba(37,99,235,0.4) !important;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] { color: #C9A84C !important; }
</style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def bar_color(score: int) -> str:
    if score >= 70:
        return "#10b981"
    if score >= 45:
        return "#f59e0b"
    return "#ef4444"


def analyze_pitch(pdf_text: str, api_key: str) -> dict:
    """Send pitch text to DeepSeek, get back structured analysis."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    system_prompt = """You are a senior partner at a top-tier VC firm (e.g. a16z, Sequoia, YC).
You evaluate startup pitch decks with sharp, candid judgment.
Return ONLY valid JSON with exactly this structure — no markdown, no explanation:

{
  "overall_score": <integer 0-100>,
  "verdict": "<INVEST|MONITOR|PASS>",
  "one_liner": "<one sentence summary of the startup>",
  "sections": {
    "problem": {"score": <0-100>, "comment": "<2 sentences>"},
    "solution": {"score": <0-100>, "comment": "<2 sentences>"},
    "market":   {"score": <0-100>, "comment": "<2 sentences>"},
    "traction": {"score": <0-100>, "comment": "<2 sentences>"},
    "team":     {"score": <0-100>, "comment": "<2 sentences>"},
    "financials":{"score": <0-100>, "comment": "<2 sentences>"}
  },
  "red_flags": [
    "<specific concern 1>",
    "<specific concern 2>",
    "<specific concern 3>",
    "<specific concern 4>",
    "<specific concern 5>"
  ],
  "comparables": [
    {"name": "<company>", "description": "<why comparable & what happened to them>"},
    {"name": "<company>", "description": "<why comparable & what happened to them>"},
    {"name": "<company>", "description": "<why comparable & what happened to them>"}
  ],
  "suggestions": [
    "<actionable improvement 1>",
    "<actionable improvement 2>",
    "<actionable improvement 3>",
    "<actionable improvement 4>",
    "<actionable improvement 5>"
  ]
}

Rules:
- Be brutally honest. Most pitches score 40-65. Reserve 80+ for exceptional decks.
- Verdict: INVEST if >= 72, MONITOR if 50-71, PASS if < 50.
- Red flags must be specific to THIS deck, not generic.
- Comparables should be real companies the judges will recognize.
- Suggestions must be concrete and actionable.
"""

    user_msg = f"""PITCH DECK TEXT (extracted from PDF):

{pdf_text[:12000]}

Analyze this pitch deck and return the JSON."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if model adds them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def render_score_card(result: dict):
    score = result["overall_score"]
    verdict = result["verdict"]

    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-number">{score}</div>
            <div class="score-label">VC Score / 100</div>
            <div>
                <span class="verdict-badge verdict-{verdict}">{verdict}</span>
            </div>
            <p style="color:#94a3b8;margin-top:1rem;font-style:italic;font-size:0.9rem;">
                "{result.get('one_liner','')}"
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_bars(sections: dict):
    st.markdown('<div class="ps-section-title">Section Breakdown</div>', unsafe_allow_html=True)
    bars_html = ""
    for key, val in sections.items():
        s = val["score"]
        color = bar_color(s)
        bars_html += f"""
        <div class="section-row">
            <span class="section-name">{key.capitalize()}</span>
            <div class="bar-bg"><div class="bar-fill" style="width:{s}%;background:{color};"></div></div>
            <span class="section-score">{s}</span>
        </div>
        """
    st.markdown(bars_html, unsafe_allow_html=True)

    # Section comments in expander
    with st.expander("📋 Section Comments"):
        for key, val in sections.items():
            st.markdown(f"**{key.capitalize()}** — {val['comment']}")


def render_red_flags(flags: list):
    st.markdown('<div class="ps-section-title">🚩 Red Flags</div>', unsafe_allow_html=True)
    flags_html = "".join(
        f'<div class="flag-card">⚠ {flag}</div>' for flag in flags
    )
    st.markdown(flags_html, unsafe_allow_html=True)


def render_comparables(comparables: list):
    st.markdown('<div class="ps-section-title">🔍 Comparable Companies</div>', unsafe_allow_html=True)
    comp_html = ""
    for c in comparables:
        comp_html += f"""
        <div class="comparable-card">
            <div class="comparable-name">{c['name']}</div>
            <div class="comparable-desc">{c['description']}</div>
        </div>
        """
    st.markdown(comp_html, unsafe_allow_html=True)


def render_suggestions(suggestions: list):
    st.markdown('<div class="ps-section-title">💡 Improvement Suggestions</div>', unsafe_allow_html=True)
    sug_html = "".join(
        f'<div class="suggestion-card">→ {s}</div>' for s in suggestions
    )
    st.markdown(sug_html, unsafe_allow_html=True)


# ── Main App ───────────────────────────────────────────────────────────────

def main():
    # Hero
    st.markdown(
        """
        <div class="hero">
            <h1>Pitch<span>Scan</span></h1>
            <p>Upload your pitch deck. Get a VC-grade analysis in 30 seconds —
            score, red flags, comparables, and concrete improvements.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API key — try secrets first, fall back to sidebar input
    api_key = None
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        pass

    if not api_key:
        with st.sidebar:
            st.markdown("### 🔑 DeepSeek API Key")
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="sk-...",
                help="Your DeepSeek API key. Get one at platform.deepseek.com",
            )
            st.caption("The key is used only for this session and is never stored.")

    # Upload
    col_upload, col_gap = st.columns([3, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "Drop your pitch deck PDF here",
            type=["pdf"],
            help="We accept standard PDF pitch decks (max 20 MB)",
        )
        st.markdown(
            '<div class="upload-hint">Supports any PDF pitch deck · Analysis takes ~15–30 seconds</div>',
            unsafe_allow_html=True,
        )

    if not uploaded_file:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            "⬆️  Upload a PDF pitch deck to get started. "
            "PitchScan reads the content and returns an instant VC-grade review.",
            icon=None,
        )
        _render_sample_metrics()
        return

    if not api_key:
        st.warning("Add your DeepSeek API key in the sidebar to run the analysis.", icon="🔑")
        return

    # Run analysis
    if "result" not in st.session_state or st.session_state.get("last_file") != uploaded_file.name:
        with st.spinner("Reading pitch deck…"):
            try:
                pdf_bytes = uploaded_file.read()
                pitch_text = extract_text_from_pdf(pdf_bytes)
            except Exception as e:
                st.error(f"Could not read PDF: {e}")
                return

        if not pitch_text.strip():
            st.error("The PDF appears to be image-only or has no extractable text. Please use a text-based PDF.")
            return

        progress = st.progress(0, text="Analyzing with DeepSeek…")

        try:
            progress.progress(20, text="Sending to VC analysis model…")
            result = analyze_pitch(pitch_text, api_key)
            progress.progress(90, text="Formatting results…")
            st.session_state["result"] = result
            st.session_state["last_file"] = uploaded_file.name
            progress.progress(100, text="Done!")
            progress.empty()
        except json.JSONDecodeError as e:
            st.error(f"Model returned invalid JSON: {e}. Please try again.")
            return
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            return
    else:
        result = st.session_state["result"]

    result = st.session_state["result"]

    st.markdown("---")

    # Layout: score card left, section bars right
    col_score, col_sections = st.columns([1, 2])
    with col_score:
        render_score_card(result)
    with col_sections:
        render_section_bars(result.get("sections", {}))

    st.markdown("---")

    # Red flags + Suggestions side by side
    col_flags, col_sug = st.columns(2)
    with col_flags:
        render_red_flags(result.get("red_flags", []))
    with col_sug:
        render_suggestions(result.get("suggestions", []))

    st.markdown("---")

    render_comparables(result.get("comparables", []))

    st.markdown("<br>", unsafe_allow_html=True)

    # Download JSON
    st.download_button(
        label="⬇️  Download Full Report (JSON)",
        data=json.dumps(result, indent=2),
        file_name=f"pitchscan_{uploaded_file.name.replace('.pdf','')}.json",
        mime="application/json",
    )

    # Re-analyze button
    if st.button("🔄 Analyze Another Deck"):
        for k in ("result", "last_file"):
            st.session_state.pop(k, None)
        st.rerun()

    # Footer
    st.markdown(
        """
        <div style="text-align:center;margin-top:3rem;color:#334155;font-size:0.78rem;">
            PitchScan · Built for World Product Day Hackathon 2026 · Powered by DeepSeek AI
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sample_metrics():
    """Show placeholder stats on the empty state."""
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("🎯", "VC Score", "0–100"),
        ("🚩", "Red Flags", "Detected"),
        ("🔍", "Comparables", "3 Companies"),
        ("💡", "Suggestions", "5 Actions"),
    ]
    for col, (icon, label, val) in zip([c1, c2, c3, c4], metrics):
        col.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                        border-radius:10px;padding:1rem;text-align:center;">
                <div style="font-size:1.6rem;">{icon}</div>
                <div style="color:#94a3b8;font-size:0.78rem;margin-top:0.3rem;">{label}</div>
                <div style="color:#e2e8f0;font-weight:600;margin-top:0.1rem;">{val}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
