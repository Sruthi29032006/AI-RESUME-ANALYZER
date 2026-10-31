"""Streamlit UI for the AI Resume Analyzer. Run: streamlit run app.py"""
import hashlib

import pandas as pd
import streamlit as st

from analyzer import AnalyzerError, analyze_resume, build_report_markdown
from ats_scorer import score_resume
from resume_parser import ResumeParseError, extract_text
from utils.validators import validate_file, validate_job_description, validate_resume_text

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.markdown("""<style>
.hero{background:linear-gradient(120deg,#4f46e5,#7c3aed);padding:1.6rem 2rem;border-radius:14px;color:#fff;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.3rem 0 0;opacity:.9}
.chip{display:inline-block;padding:3px 10px;margin:2px;border-radius:999px;font-size:.85rem}
.ok{background:#dcfce7;color:#166534}.bad{background:#fee2e2;color:#991b1b}.mid{background:#fef9c3;color:#854d0e}.rec{background:#e0e7ff;color:#3730a3}
</style>""", unsafe_allow_html=True)


def chips(items, css):
    st.markdown("".join(f'<span class="chip {css}">{i}</span>' for i in items) if items else "_None_",
                unsafe_allow_html=True)


with st.sidebar:
    st.header("About")
    st.write("Compares your resume with a job description using keyword matching (Python) "
             "and semantic review (Google Gemini).")
    st.info("🔒 Resumes contain personal data. Files are processed in memory and not saved. "
            "The resume text is sent to Google's Gemini API for analysis.")
    st.caption("The ATS score is an estimate, not a score from a commercial ATS.")

st.markdown('<div class="hero"><h1>📄 AI Resume Analyzer</h1>'
            '<p>Estimate ATS compatibility, find keyword gaps, and get honest improvement tips.</p></div>',
            unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    st.subheader("1. Upload resume")
    upload = st.file_uploader("PDF or DOCX (max 5 MB)", type=["pdf", "docx"])
with right:
    st.subheader("2. Paste job description")
    jd = st.text_area("Job description", height=220, label_visibility="collapsed",
                      placeholder="Paste the full job description here...")

if st.button("🔍 Analyze Resume", type="primary", use_container_width=True):
    ok, msg = (False, "Please upload a resume.") if upload is None else validate_file(upload.name, upload.size)
    if ok:
        ok, msg = validate_job_description(jd)
    if not ok:
        st.error(msg)
    else:
        try:
            data = upload.getvalue()
            with st.spinner("Reading resume..."):
                resume = extract_text(upload.name, data)
            ok, msg = validate_resume_text(resume)
            if not ok:
                st.error(msg)
            else:
                key = hashlib.sha256((resume + "||" + jd).encode()).hexdigest()
                cached = st.session_state.get("result")
                if cached and cached["key"] == key and cached["ai"]:
                    pass  # same inputs: reuse, avoids a repeat API call
                else:
                    score = score_resume(resume, jd)
                    ai, ai_error = None, None
                    with st.spinner("Asking Gemini for a detailed review..."):
                        try:
                            ai = analyze_resume(resume, jd, score)
                        except AnalyzerError as e:
                            ai_error = str(e)
                    st.session_state["result"] = {"key": key, "resume": resume, "score": score,
                                                  "ai": ai, "ai_error": ai_error}
        except ResumeParseError as e:
            st.error(str(e))
        except Exception:
            st.error("Something went wrong while processing your files. Please try again.")

res = st.session_state.get("result")
if res:
    score, ai = res["score"], res["ai"]
    st.divider()
    c1, c2 = st.columns([1, 2])
    c1.metric("Estimated ATS match", f"{score['overall']}/100")
    c1.progress(score["overall"] / 100)
    c1.caption("Estimate based on keyword matching - not a real ATS score.")
    df = pd.DataFrame({"Category": list(score["breakdown"]),
                       "Percent": [round(100 * e / m) for e, m in score["breakdown"].values()]}).set_index("Category")
    c2.bar_chart(df, height=230)
    for n in score["notes"]:
        st.warning(n)
    if res["ai_error"]:
        st.warning(f"AI review unavailable: {res['ai_error']} Keyword score above still works.")
    with st.expander("Extracted resume text (check it looks right)"):
        st.text(res["resume"])

    t1, t2, t3, t4 = st.tabs(["🔑 Keywords", "🧠 AI Analysis", "✍️ Bullet Points", "✅ Recommendations"])
    with t1:
        a, b, c = st.columns(3)
        a.markdown("**Matching**"); chips(score["matching"], "ok")
        b.markdown("**Missing**"); chips(score["missing"], "bad")
        b.markdown("**Partial** (related skill present)"); chips(score["partial"], "mid")
        c.markdown("**Recommended (from job text)**"); chips(score["recommended"], "rec")
        if ai and ai["keyword_notes"]:
            st.markdown("##### Why these matter")
            for k in ai["keyword_notes"]:
                tag = "✅ already shown in resume" if k["status"] == "demonstrated" else "📚 learn before adding"
                st.markdown(f"**{k['keyword']}** ({tag}): {k['why_it_matters']}")
    with t2:
        if ai:
            st.write(ai["overall_assessment"])
            for title, key in [("Strengths", "strengths"), ("Weaknesses", "weaknesses"),
                               ("Irrelevant content", "irrelevant_content"), ("Writing issues", "writing_issues")]:
                with st.expander(title, expanded=key == "strengths"):
                    for x in ai[key] or ["Nothing notable."]:
                        st.markdown(f"- {x}")
        else:
            st.info("AI analysis not available.")
    with t3:
        if ai and ai["bullet_improvements"]:
            st.caption("⚠️ Drafts only - verify every line is true before using it.")
            h1, h2 = st.columns(2); h1.markdown("**Original**"); h2.markdown("**Improved (draft)**")
            for bp in ai["bullet_improvements"]:
                x, y = st.columns(2); x.write(bp["original"]); y.success(bp["improved"])
        else:
            st.info("No bullet suggestions available.")
    with t4:
        if ai:
            st.markdown("##### Top 5 recommendations")
            for i, r in enumerate(ai["top_recommendations"][:5], 1):
                st.markdown(f"{i}. {r}")
            for title, key in [("Missing technical skills (learn first)", "missing_technical_skills"),
                               ("Formatting & readability", "formatting_suggestions"),
                               ("Role-specific preparation", "role_preparation")]:
                with st.expander(title):
                    for x in ai[key] or ["Nothing notable."]:
                        st.markdown(f"- {x}")
        else:
            st.info("AI recommendations not available.")
    st.download_button("⬇️ Download report (.md)", build_report_markdown(score, ai),
                       file_name="resume_report.md", mime="text/markdown")
