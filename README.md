# AI Resume Analyzer
Upload a resume (PDF/DOCX), paste a job description, and get an **estimated** ATS score, keyword gaps, and AI-written feedback.
The score is computed in Python (explainable keyword matching); Google Gemini adds semantic review and bullet rewrites.
It never claims to be a real ATS score, and the prompt forbids inventing skills or metrics.

## Files
| File | Role |
|---|---|
| app.py | Streamlit UI |
| resume_parser.py | PDF/DOCX text extraction |
| ats_scorer.py | Score out of 100 (skills 50, keywords 20, role 10, education 10, experience 10) |
| analyzer.py | Gemini prompt, call, JSON parsing + validation, error handling |
| utils/validators.py | File/text validation |
| tests/test_all.py | Unit tests |

## Setup (Windows PowerShell, VS Code)
```powershell
cd AI-Resume-Analyzer
python -m venv venv
.\venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
```
Get a free key at https://aistudio.google.com/apikey, then edit `.env`:
```
GEMINI_API_KEY=your_real_key
```
Run: `streamlit run app.py`   Test: `python -m unittest discover -s tests -t . -v`

## Troubleshooting
- *GEMINI_API_KEY is missing*: key not saved in `.env`; restart Streamlit after editing.
- *Model not found / 404*: set `GEMINI_MODEL` in `.env` to a currently available Gemini Flash model.
- *Rate limit*: free tier is limited; wait a minute.
- *Scanned PDF has no text*: use a text-based PDF or DOCX (no OCR).

## GitHub
```
git init
git add .
git commit -m "Initial commit: AI Resume Analyzer"
git branch -M main
git remote add origin https://github.com/<you>/AI-Resume-Analyzer.git
git push -u origin main
```
`.env` is git-ignored; never commit your key.

## Privacy
Resumes are processed in memory only and not logged. Resume text is sent to Google's Gemini API.

## Screenshots
_Add screenshots here after running the app._

## Future work
OCR for scanned PDFs, semantic embeddings, multiple-resume comparison, user accounts.
