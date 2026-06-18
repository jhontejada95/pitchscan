# PitchScan — Deploy to Streamlit Cloud (5 min)

## 1. Push to GitHub

```bash
# From your computer — create a NEW repo named "pitchscan" on github.com first, then:
cd path/to/pitchscan
git init
git add app.py requirements.txt .gitignore .streamlit/secrets.toml.example
git commit -m "feat: PitchScan MVP"
git branch -M main
git remote add origin https://github.com/jhontejada95/pitchscan.git
git push -u origin main
```

> **DO NOT** add `.streamlit/secrets.toml` — it's gitignored for a reason.

---

## 2. Connect Streamlit Cloud

1. Go to **share.streamlit.io** → Sign in with GitHub
2. Click **"New app"**
3. Fill in:
   - Repository: `jhontejada95/pitchscan`
   - Branch: `main`
   - Main file path: `app.py`
4. Click **"Deploy!"**

---

## 3. Set your DeepSeek API Key (secret)

1. In Streamlit Cloud, open your app → **⚙️ Settings → Secrets**
2. Add:
   ```toml
   DEEPSEEK_API_KEY = "sk-your-actual-key-here"
   ```
3. Click **Save** — the app reboots automatically.

---

## 4. Get your public URL

Your app will be live at:
```
https://jhontejada95-pitchscan-app-xxxxxx.streamlit.app
```

Copy this URL — you need it for the hackathon submission.

---

## 5. Hackathon submission checklist

- [ ] App is live at Streamlit Cloud URL
- [ ] Tested with a real PDF pitch deck
- [ ] Screenshot of Novus.ai dashboard showing analytics firing
- [ ] 2-min demo video (record screen + narrate the workflow)
- [ ] Submit at: **mindtheproduct.devpost.com**

---

## Local testing (optional)

```bash
pip install streamlit openai pdfplumber
# Create .streamlit/secrets.toml with your key
streamlit run app.py
```
