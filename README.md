# PitchScan 🎯

**AI-powered VC-grade analysis for startup pitch decks.**

Upload a PDF → get a score, verdict, red flags, comparables, and 5 concrete improvements — in minutes. Built for the [World Product Day Hackathon 2026](https://mindtheproduct.devpost.com/).

**Live app:** [pitchscan.streamlit.app](https://pitchscan.streamlit.app)  
**Landing page:** [jhontejada95.github.io/pitchscan](https://jhontejada95.github.io/pitchscan)

---

## What it does

PitchScan reads your pitch deck the way a VC partner does — brutally, specifically, with no interest in making you feel good.

| Output | Detail |
|---|---|
| **VC Score (0–100)** | Weighted across 6 dimensions. 80+ is exceptional. Most decks score 40–65. |
| **Verdict** | INVEST (≥72) · MONITOR (50–71) · PASS (<50) |
| **Section Breakdown** | Problem, Solution, Market, Traction, Team, Financials — scored + 2-sentence comment each |
| **Red Flags** | 5 specific issues found in *your* deck, not generic advice |
| **Comparables** | 3 real companies investors will benchmark you against |
| **Improvements** | 5 concrete rewrites and additions to make before your next pitch |
| **Export** | JSON · Markdown · Word (DOCX) |

---

## New in v2

- **Survey context** — add stage, sector, revenue status, and target investor type for a sharper, calibrated analysis
- **Investor persona** — choose YC, a16z, Sequoia, or Benchmark; each changes the evaluation lens and voice
- **Animated gauge** — score arc draws itself from 0 in 1.5s
- **Deck counter** — live count of decks analyzed shown in hero
- **Feedback** — 👍/👎 at the bottom of every result

---

## Stack

- **Frontend / App** — [Streamlit](https://streamlit.io) 1.35+
- **AI** — [DeepSeek](https://deepseek.com) Chat API (OpenAI-compatible)
- **PDF extraction** — `pdfplumber` (text) + `pytesseract` + `pdf2image` (OCR fallback)
- **Reports** — `python-docx`
- **Analytics** — Novus.ai + Pendo

---

## Run locally

```bash
git clone https://github.com/jhontejada95/pitchscan.git
cd pitchscan
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
DEEPSEEK_API_KEY = "sk-..."
```

```bash
streamlit run app.py
```

> Requires `tesseract-ocr` and `poppler-utils` for OCR on image-only PDFs.
> On macOS: `brew install tesseract poppler`
> On Ubuntu: `sudo apt install tesseract-ocr poppler-utils`

---

## Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select your fork → `app.py`
3. Under **Advanced settings → Secrets**, add:
   ```
   DEEPSEEK_API_KEY = "sk-..."
   ```
4. Deploy — no other config needed

---

## Project structure

```
pitchscan/
├── app.py              # Streamlit app (all logic)
├── landing.html        # Static landing page (GitHub Pages)
├── requirements.txt    # Python dependencies
├── packages.txt        # System packages (tesseract, poppler)
└── runtime.txt         # Python version hint
```

---

## License

MIT — build on it, fork it, ship something better.

---

*Built in 48 hours for World Product Day Hackathon 2026 · Powered by DeepSeek AI*
