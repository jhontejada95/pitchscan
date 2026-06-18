import streamlit as st
import json
import re
import io
import random
from openai import OpenAI

st.set_page_config(
    page_title="PitchScan - VC-Grade Pitch Analysis",
    page_icon="PS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

NOVUS_APP_ID = "26e1d6da-25ad-4964-981b-411e2faef7b0"

VC_TIPS = [
    ("Paul Graham (YC)", "The best decks tell a story, not a business plan. Lead with a specific customer who has a painful problem."),
    ("Sequoia Capital", "Answer 'Why Now?' — timing kills more startups than bad products. Show why this moment is the right moment."),
    ("a16z", "Investors fund people first, ideas second. Spend at least 20% of your deck on team and unfair advantage."),
    ("First Round Capital", "Revenue > users > engagement > TAM claims. Show real traction even if it's small."),
    ("Bill Gurley (Benchmark)", "Unit economics must work at current scale before you pour fuel on the fire. Show CAC/LTV explicitly."),
    ("YC Advice", "Keep it under 12 slides. Every slide should answer one question, clearly. Complexity signals confusion."),
    ("Sequoia Capital", "Never claim 'no competition' — it tells investors either there's no market or you haven't looked hard enough."),
    ("Mike Maples Jr.", "The best pitches have a 'Why Now' insight that feels inevitable in hindsight but non-obvious today."),
    ("David Sacks (Craft)", "A hockey stick without explaining the inflection point is a red flag. What changed? Why then?"),
    ("Elad Gil", "Net Dollar Retention above 110% is one of the strongest signals for a B2B Series A. Show cohort retention."),
    ("YC Advice", "Your ask must be specific: '$X to reach Y milestone in Z months.' Vague asks signal vague thinking."),
    ("Sequoia Capital", "Three durable moats: network effects, switching costs, unique proprietary data. Show which one is yours."),
    ("Peter Thiel", "Aim to be the last company in your market — not just better, but 10x better in a way that matters."),
    ("Sarah Tavel (Benchmark)", "The competition slide matrix where you win every column is not credible. Pick 2-3 dimensions you truly own."),
    ("Greylock Partners", "Product-market fit evidence: retention curves that flatten, strong NPS, customers who pay and refer others."),
    ("YC Advice", "Gross margin matters more than revenue. 80%+ gross margin in SaaS signals real leverage in the model."),
    ("Fred Wilson (USV)", "Show the market size bottom-up, not top-down. A slice of a massive SAM number is never convincing."),
    ("a16z", "Distribution is the new product. Show how you acquire customers cheaply and at scale — not just that you can build."),
    ("Marc Andreessen", "Software is eating the world — but only when the timing, team, and distribution align. Prove all three."),
    ("Benchmark Capital", "The best founders know exactly what they don't know. Intellectual honesty in a pitch is a feature, not a bug."),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
*{box-sizing:border-box;}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#050a14;color:#e2e8f0;}
section[data-testid="stSidebar"]{background:#070d1a;}
header[data-testid="stHeader"]{display:none!important;}
footer{display:none!important;}
.block-container{max-width:1040px;padding:0 1.5rem 3rem;}

/* Hero */
.ps-hero{text-align:center;padding:3.5rem 1rem 2rem;}
.ps-hero-badge{display:inline-block;background:rgba(201,168,76,0.1);border:1px solid rgba(201,168,76,0.3);
  color:#C9A84C;font-size:0.72rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;
  padding:0.3rem 1rem;border-radius:99px;margin-bottom:1.2rem;}
.ps-hero h1{font-size:3rem;font-weight:800;color:#fff;margin:0 0 1rem;line-height:1.1;}
.ps-hero h1 span{background:linear-gradient(135deg,#C9A84C,#f0d080);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.ps-hero p{color:#64748b;font-size:1.05rem;max-width:560px;margin:0 auto 2rem;line-height:1.7;}

/* Upload */
.ps-upload-wrap{background:rgba(255,255,255,0.02);border:1.5px dashed rgba(201,168,76,0.3);
  border-radius:16px;padding:2rem;transition:border-color 0.2s;}
[data-testid="stFileUploader"]{background:transparent!important;border:none!important;padding:0!important;}
.ps-upload-hint{color:#475569;font-size:0.8rem;text-align:center;margin-top:0.8rem;}

/* Tips carousel */
.ps-tips-box{background:rgba(37,99,235,0.06);border:1px solid rgba(37,99,235,0.2);
  border-radius:12px;padding:1.4rem 1.6rem;margin:1.5rem 0;position:relative;min-height:90px;}
.ps-tips-source{font-size:0.7rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
  color:#2563EB;margin-bottom:0.4rem;}
.ps-tips-text{color:#94a3b8;font-size:0.9rem;line-height:1.6;font-style:italic;}
.ps-tips-counter{position:absolute;bottom:0.8rem;right:1rem;font-size:0.65rem;color:#334155;
  font-family:'Fira Code',monospace;}

/* Score gauge */
.ps-gauge-wrap{display:flex;flex-direction:column;align-items:center;padding:1.5rem;}
.ps-gauge-svg{filter:drop-shadow(0 0 20px rgba(201,168,76,0.3));}
.ps-gauge-score{font-size:3.2rem;font-weight:800;fill:url(#gold-grad);font-family:'Fira Code',monospace;}
.ps-gauge-label{font-size:0.7rem;fill:#475569;text-transform:uppercase;letter-spacing:2px;}

.verdict-chip{display:inline-flex;align-items:center;gap:0.4rem;
  padding:0.45rem 1.2rem;border-radius:99px;font-size:0.85rem;font-weight:600;
  letter-spacing:0.5px;margin-top:1rem;}
.verdict-INVEST {background:rgba(16,185,129,0.12);color:#10b981;border:1px solid rgba(16,185,129,0.4);}
.verdict-MONITOR{background:rgba(245,158,11,0.12);color:#f59e0b;border:1px solid rgba(245,158,11,0.4);}
.verdict-PASS   {background:rgba(239,68,68,0.12); color:#ef4444;border:1px solid rgba(239,68,68,0.4);}
.verdict-dot{width:6px;height:6px;border-radius:50%;background:currentColor;}

/* Section bars */
.ps-bars{padding:0.5rem 0;}
.ps-bar-row{display:flex;align-items:center;gap:0.8rem;margin-bottom:0.65rem;}
.ps-bar-name{min-width:100px;font-size:0.78rem;color:#64748b;text-transform:capitalize;font-weight:500;}
.ps-bar-bg{flex:1;height:6px;background:rgba(255,255,255,0.05);border-radius:99px;overflow:hidden;}
.ps-bar-fill{height:100%;border-radius:99px;}
.ps-bar-score{min-width:30px;text-align:right;font-size:0.75rem;font-family:'Fira Code',monospace;color:#94a3b8;}

/* Section heading */
.ps-sh{font-size:0.7rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
  color:#475569;margin:2rem 0 0.8rem;padding-bottom:0.5rem;
  border-bottom:1px solid rgba(255,255,255,0.05);}

/* Cards */
.ps-flag{background:rgba(239,68,68,0.05);border-left:2px solid #ef4444;
  border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin-bottom:0.4rem;
  font-size:0.83rem;color:#fca5a5;line-height:1.5;}
.ps-sug{background:rgba(16,185,129,0.05);border-left:2px solid #10b981;
  border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin-bottom:0.4rem;
  font-size:0.83rem;color:#6ee7b7;line-height:1.5;}
.ps-comp{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
  border-radius:10px;padding:0.9rem 1rem;margin-bottom:0.5rem;}
.ps-comp-name{color:#C9A84C;font-weight:600;font-size:0.9rem;}
.ps-comp-desc{color:#64748b;font-size:0.82rem;margin-top:0.25rem;line-height:1.5;}

/* Divider */
hr{border-color:rgba(255,255,255,0.05)!important;}

/* Download bar */
.ps-dl-bar{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
  border-radius:12px;padding:1.2rem 1.5rem;display:flex;align-items:center;
  gap:1rem;margin-top:1.5rem;}
.ps-dl-label{color:#475569;font-size:0.8rem;font-weight:600;letter-spacing:1px;
  text-transform:uppercase;margin-right:auto;}

/* Buttons */
.stDownloadButton>button,.stButton>button{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid rgba(255,255,255,0.12)!important;
  color:#e2e8f0!important;border-radius:8px!important;
  font-size:0.83rem!important;font-weight:500!important;padding:0.5rem 1.2rem!important;}
.stDownloadButton>button:hover,.stButton>button:hover{
  background:rgba(255,255,255,0.08)!important;
  border-color:rgba(201,168,76,0.4)!important;color:#C9A84C!important;}

/* One-liner */
.ps-oneliner{color:#64748b;font-size:0.88rem;font-style:italic;
  text-align:center;margin-top:0.8rem;line-height:1.6;padding:0 1rem;}

/* Sidebar */
[data-testid="stSidebar"] .stTextInput input{
  background:rgba(255,255,255,0.04)!important;border:1px solid rgba(255,255,255,0.1)!important;
  color:#e2e8f0!important;border-radius:8px!important;}
</style>
"""

TIPS_JS = """
<script>
(function(){
  var tips = TIPS_PLACEHOLDER;
  var i = 0;
  function show(){
    var t = tips[i % tips.length];
    var src = document.getElementById('ps-tip-src');
    var txt = document.getElementById('ps-tip-txt');
    var cnt = document.getElementById('ps-tip-cnt');
    if(src && txt && cnt){
      src.style.opacity=0; txt.style.opacity=0;
      setTimeout(function(){
        src.textContent = t[0];
        txt.textContent = '“' + t[1] + '”';
        cnt.textContent = (i%tips.length+1) + ' / ' + tips.length;
        src.style.transition='opacity 0.5s'; txt.style.transition='opacity 0.5s';
        src.style.opacity=1; txt.style.opacity=1;
      },300);
    }
    i++;
  }
  show();
  setInterval(show, 6000);
})();
</script>
"""


def make_tips_js():
    tips_json = json.dumps([[t[0], t[1]] for t in VC_TIPS])
    return TIPS_JS.replace("TIPS_PLACEHOLDER", tips_json)


def render_loading_tips():
    first = VC_TIPS[0]
    html = (
        '<div class="ps-tips-box">'
        '<div class="ps-tips-source" id="ps-tip-src">' + first[0] + '</div>'
        '<div class="ps-tips-text" id="ps-tip-txt">“' + first[1] + '”</div>'
        '<div class="ps-tips-counter" id="ps-tip-cnt">1 / ' + str(len(VC_TIPS)) + '</div>'
        '</div>'
        + make_tips_js()
    )
    st.markdown(html, unsafe_allow_html=True)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    native_text = "\n\n".join(text_parts).strip()
    if len(native_text) >= 150:
        return native_text
    # OCR fallback
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        st.info("Image-based PDF detected — running OCR...", icon="🔍")
        images = convert_from_bytes(file_bytes, dpi=200)
        ocr_parts = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="eng")
            if text.strip():
                ocr_parts.append(text.strip())
        ocr_text = "\n\n".join(ocr_parts).strip()
        return ocr_text if ocr_text else native_text
    except ImportError as e:
        st.error(f"OCR library missing: {e}")
        return native_text
    except Exception as e:
        import traceback
        st.error(f"OCR error: {type(e).__name__}: {e}")
        st.code(traceback.format_exc())
        return native_text


def analyze_pitch(pdf_text: str, api_key: str) -> dict:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    system_prompt = (
        "You are a senior partner at a top-tier VC firm (a16z, Sequoia, YC). "
        "Evaluate startup pitch decks with sharp, candid judgment. "
        "Return ONLY valid JSON with exactly this structure, no markdown:\n\n"
        '{"overall_score":<0-100>,"verdict":"<INVEST|MONITOR|PASS>",'
        '"one_liner":"<one sentence>","sections":{"problem":{"score":<0-100>,"comment":"<2 sentences>"},'
        '"solution":{"score":<0-100>,"comment":"<2 sentences>"},'
        '"market":{"score":<0-100>,"comment":"<2 sentences>"},'
        '"traction":{"score":<0-100>,"comment":"<2 sentences>"},'
        '"team":{"score":<0-100>,"comment":"<2 sentences>"},'
        '"financials":{"score":<0-100>,"comment":"<2 sentences>"}},'
        '"red_flags":["<1>","<2>","<3>","<4>","<5>"],'
        '"comparables":[{"name":"<co>","description":"<why>"},{"name":"<co>","description":"<why>"},'
        '{"name":"<co>","description":"<why>"}],'
        '"suggestions":["<1>","<2>","<3>","<4>","<5>"]}\n\n'
        "Rules: Be brutally honest. Most decks score 40-65. Reserve 80+ for exceptional. "
        "Verdict: INVEST>=72, MONITOR 50-71, PASS<50. Red flags must be specific to this deck."
    )
    user_msg = f"PITCH DECK:\n\n{pdf_text[:12000]}\n\nReturn the JSON analysis."
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}],
        temperature=0.3, max_tokens=2000,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def bar_color(s):
    return "#10b981" if s >= 70 else ("#f59e0b" if s >= 45 else "#ef4444")


def make_gauge_svg(score: int) -> str:
    r = 70
    cx = cy = 90
    circumference = 2 * 3.14159 * r
    arc = circumference * 0.75
    filled = arc * (score / 100)
    gap = arc - filled
    rotation = 135
    return f"""
<svg width="180" height="180" viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg" class="ps-gauge-svg">
  <defs>
    <linearGradient id="gold-grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#f0d080"/>
    </linearGradient>
    <linearGradient id="arc-grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#2563EB"/>
      <stop offset="100%" stop-color="#C9A84C"/>
    </linearGradient>
  </defs>
  <!-- Track -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="10"
    stroke-dasharray="{arc} {circumference - arc}"
    stroke-dashoffset="0"
    stroke-linecap="round"
    transform="rotate({rotation} {cx} {cy})"/>
  <!-- Fill -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#arc-grad)" stroke-width="10"
    stroke-dasharray="{filled} {circumference - filled}"
    stroke-dashoffset="0"
    stroke-linecap="round"
    transform="rotate({rotation} {cx} {cy})"/>
  <!-- Score -->
  <text x="{cx}" y="{cy - 6}" text-anchor="middle" dominant-baseline="middle"
    font-size="36" font-weight="800" fill="url(#gold-grad)" font-family="'Fira Code',monospace">{score}</text>
  <text x="{cx}" y="{cy + 22}" text-anchor="middle"
    font-size="9" fill="#475569" font-family="Inter,sans-serif" letter-spacing="2" text-transform="uppercase">VC SCORE</text>
</svg>"""


def build_markdown_report(result: dict, filename: str) -> str:
    r = result
    score = r["overall_score"]
    verdict = r["verdict"]
    lines = [
        f"# PitchScan Report — {filename}",
        "",
        f"**Overall Score:** {score} / 100  ",
        f"**Verdict:** {verdict}  ",
        f"**Summary:** {r.get('one_liner', '')}",
        "",
        "---",
        "",
        "## Section Breakdown",
        "",
    ]
    for key, val in r.get("sections", {}).items():
        lines.append(f"### {key.capitalize()} — {val['score']}/100")
        lines.append(val["comment"])
        lines.append("")

    lines += ["---", "", "## Red Flags", ""]
    for flag in r.get("red_flags", []):
        lines.append(f"- ⚠ {flag}")

    lines += ["", "---", "", "## Comparable Companies", ""]
    for c in r.get("comparables", []):
        lines.append(f"**{c['name']}** — {c['description']}")
        lines.append("")

    lines += ["---", "", "## Improvement Suggestions", ""]
    for s in r.get("suggestions", []):
        lines.append(f"- → {s}")

    lines += ["", "---", "", "*Generated by PitchScan · Powered by DeepSeek AI*"]
    return "\n".join(lines)


def build_docx_report(result: dict, filename: str) -> bytes:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"

    title = doc.add_heading(f"PitchScan Report", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"File: {filename}")
    doc.add_paragraph(f"Overall Score: {result['overall_score']} / 100")
    doc.add_paragraph(f"Verdict: {result['verdict']}")
    doc.add_paragraph(f"Summary: {result.get('one_liner','')}")
    doc.add_paragraph("")

    doc.add_heading("Section Breakdown", 1)
    for key, val in result.get("sections", {}).items():
        p = doc.add_paragraph()
        run = p.add_run(f"{key.capitalize()} — {val['score']}/100")
        run.bold = True
        doc.add_paragraph(val["comment"])

    doc.add_heading("Red Flags", 1)
    for flag in result.get("red_flags", []):
        doc.add_paragraph(f"⚠ {flag}", style="List Bullet")

    doc.add_heading("Comparable Companies", 1)
    for c in result.get("comparables", []):
        p = doc.add_paragraph()
        p.add_run(c["name"] + " — ").bold = True
        p.add_run(c["description"])

    doc.add_heading("Improvement Suggestions", 1)
    for s in result.get("suggestions", []):
        doc.add_paragraph(f"→ {s}", style="List Bullet")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def render_results(result: dict, filename: str):
    score = result["overall_score"]
    verdict = result["verdict"]
    one_liner = result.get("one_liner", "")

    # Top row: gauge + sections
    col_g, col_s = st.columns([1, 2])
    with col_g:
        st.markdown(
            f'<div class="ps-gauge-wrap">'
            f'{make_gauge_svg(score)}'
            f'<div><span class="verdict-chip verdict-{verdict}">'
            f'<span class="verdict-dot"></span>{verdict}'
            f'</span></div>'
            f'<div class="ps-oneliner">{one_liner}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_s:
        st.markdown('<div class="ps-sh">Section Breakdown</div>', unsafe_allow_html=True)
        bars = ""
        for key, val in result.get("sections", {}).items():
            s = val["score"]
            color = bar_color(s)
            bars += (
                f'<div class="ps-bar-row">'
                f'<span class="ps-bar-name">{key.capitalize()}</span>'
                f'<div class="ps-bar-bg"><div class="ps-bar-fill" style="width:{s}%;background:{color};"></div></div>'
                f'<span class="ps-bar-score">{s}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="ps-bars">{bars}</div>', unsafe_allow_html=True)
        with st.expander("View section comments"):
            for key, val in result.get("sections", {}).items():
                st.markdown(f"**{key.capitalize()}** — {val['comment']}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Flags + Suggestions
    col_f, col_sg = st.columns(2)
    with col_f:
        st.markdown('<div class="ps-sh">Red Flags</div>', unsafe_allow_html=True)
        html = "".join(f'<div class="ps-flag">&#9888;&nbsp; {f}</div>' for f in result.get("red_flags", []))
        st.markdown(html, unsafe_allow_html=True)
    with col_sg:
        st.markdown('<div class="ps-sh">Improvement Suggestions</div>', unsafe_allow_html=True)
        html = "".join(f'<div class="ps-sug">&#8594;&nbsp; {s}</div>' for s in result.get("suggestions", []))
        st.markdown(html, unsafe_allow_html=True)

    # Comparables
    st.markdown('<div class="ps-sh">Comparable Companies</div>', unsafe_allow_html=True)
    comp_cols = st.columns(3)
    for i, c in enumerate(result.get("comparables", [])):
        with comp_cols[i % 3]:
            st.markdown(
                f'<div class="ps-comp">'
                f'<div class="ps-comp-name">{c["name"]}</div>'
                f'<div class="ps-comp-desc">{c["description"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Downloads
    st.markdown('<div class="ps-sh">Download Report</div>', unsafe_allow_html=True)
    base_name = filename.replace(".pdf", "")
    dcol1, dcol2, dcol3, _ = st.columns([1, 1, 1, 2])
    with dcol1:
        st.download_button(
            "JSON",
            data=json.dumps(result, indent=2),
            file_name=f"pitchscan_{base_name}.json",
            mime="application/json",
        )
    with dcol2:
        st.download_button(
            "Markdown",
            data=build_markdown_report(result, filename),
            file_name=f"pitchscan_{base_name}.md",
            mime="text/markdown",
        )
    with dcol3:
        try:
            docx_bytes = build_docx_report(result, filename)
            st.download_button(
                "Word (DOCX)",
                data=docx_bytes,
                file_name=f"pitchscan_{base_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception:
            pass

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Scan Another Deck"):
        for k in ("result", "last_file"):
            st.session_state.pop(k, None)
        st.rerun()


def main():
    st.markdown(f"""
<script>
(function(n,o,v,u,s,ai){{
  if(n[s])return;n[s]=Object.assign(n[s]||{{}},{{initialize:function(opts){{n[s].q=(n[s].q||[]).concat([["initialize",opts]]);}} }});
  n[s].initialize({{apiKey:"{NOVUS_APP_ID}"}});
  ai=o.createElement('script');ai.async=true;
  ai.src='https://cdn.novus.pendo.io/agent/static/{NOVUS_APP_ID}/novus.js';
  o.head.appendChild(ai);
}})(window,document,'novus','novus','novus');
</script>""", unsafe_allow_html=True)

    st.markdown(CSS, unsafe_allow_html=True)

    # Sidebar: API key
    api_key = None
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        pass
    if not api_key:
        with st.sidebar:
            st.markdown("### API Key")
            api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
            st.caption("Used only in this session.")

    # Hero
    st.markdown(
        '<div class="ps-hero">'
        '<div class="ps-hero-badge">AI-Powered VC Analysis</div>'
        '<h1>Know if your pitch will<br><span>get funded</span></h1>'
        '<p>Upload your pitch deck and get an instant, brutally honest VC-grade review — '
        'score, red flags, comparable companies, and concrete improvements.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Upload
    uploaded_file = st.file_uploader(
        "Drop your pitch deck PDF here",
        type=["pdf"],
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="ps-upload-hint">Supports text-based and image-only PDFs &middot; '
        'Analysis takes a few minutes</div>',
        unsafe_allow_html=True,
    )

    if not uploaded_file:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, icon, label, val in [
            (c1, "🎯", "VC Score", "0 – 100"),
            (c2, "🚩", "Red Flags", "Identified"),
            (c3, "🔍", "Comparables", "3 Companies"),
            (c4, "💡", "Suggestions", "5 Actions"),
        ]:
            col.markdown(
                f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);'
                f'border-radius:12px;padding:1.2rem;text-align:center;">'
                f'<div style="font-size:1.8rem;margin-bottom:0.4rem;">{icon}</div>'
                f'<div style="color:#475569;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">{label}</div>'
                f'<div style="color:#e2e8f0;font-weight:700;font-size:1rem;margin-top:0.3rem;">{val}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        return

    if not api_key:
        st.warning("Add your DeepSeek API key in the sidebar to run the analysis.")
        return

    cache_key = uploaded_file.name + str(uploaded_file.size)

    if "result" not in st.session_state or st.session_state.get("last_file") != cache_key:
        render_loading_tips()

        with st.spinner("Reading pitch deck..."):
            try:
                pdf_bytes = uploaded_file.read()
                pitch_text = extract_text_from_pdf(pdf_bytes)
            except Exception as e:
                st.error(f"Could not read PDF: {e}")
                return

        if not pitch_text.strip():
            st.error("Could not extract any text from this PDF. Try a different file.")
            return

        with st.spinner("Analyzing with DeepSeek — this takes a few minutes..."):
            try:
                result = analyze_pitch(pitch_text, api_key)
                st.session_state["result"] = result
                st.session_state["last_file"] = cache_key
            except json.JSONDecodeError as e:
                st.error(f"Model returned invalid JSON. Please try again.")
                return
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return
        st.rerun()

    render_results(st.session_state["result"], uploaded_file.name)

    st.markdown(
        '<div style="text-align:center;margin-top:2rem;color:#1e293b;font-size:0.72rem;">'
        'PitchScan &middot; World Product Day Hackathon 2026 &middot; Powered by DeepSeek AI'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
