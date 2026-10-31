"""Explainable, Python-only keyword scoring. This is an ESTIMATE, not a real ATS score."""
import re
from collections import Counter

SKILLS = {
    "python": (), "java": (), "c++": (), "c#": (), "javascript": ("js",), "typescript": (),
    "sql": (), "mysql": (), "postgresql": ("postgres",), "mongodb": (), "html": (), "css": (),
    "react": ("reactjs",), "angular": (), "vue": (), "node.js": ("nodejs", "node"),
    "flask": (), "django": (), "fastapi": (), "streamlit": (), "pandas": (), "numpy": (),
    "scikit-learn": ("sklearn",), "tensorflow": (), "pytorch": (), "keras": (),
    "machine learning": ("ml",), "deep learning": (), "natural language processing": ("nlp",),
    "computer vision": (), "data analysis": (), "data visualization": (), "statistics": (),
    "tableau": (), "power bi": ("powerbi",), "excel": (), "matplotlib": (), "seaborn": (),
    "aws": ("amazon web services",), "azure": (), "gcp": ("google cloud",), "docker": (),
    "kubernetes": (), "git": (), "github": (), "linux": (), "rest api": ("rest apis", "restful"),
    "spark": ("pyspark",), "hadoop": (), "etl": (), "airflow": (), "llm": ("llms", "large language models"),
    "generative ai": ("genai", "gen ai"), "prompt engineering": (), "ci/cd": (), "agile": (),
    "data structures": (), "algorithms": (), "oop": ("object-oriented", "object oriented"),
}
GROUPS = [
    {"tensorflow", "pytorch", "keras"}, {"mysql", "postgresql", "sql", "mongodb"},
    {"aws", "azure", "gcp"}, {"tableau", "power bi"}, {"flask", "django", "fastapi"},
    {"react", "angular", "vue"}, {"matplotlib", "seaborn"}, {"spark", "hadoop"},
]
EDU_TERMS = ("b.tech", "btech", "bachelor", "b.e", "b.sc", "bca", "m.tech", "master", "mca", "phd", "degree", "diploma")
EXP_TERMS = ("experience", "intern", "internship", "project", "projects", "developed", "built", "worked")
STOP = set("""about above after also and any are been being between both but can could does each for from have
having into more most must not our out over other should such than that the their them then there these they
this those through under until upon was were what when where which while who will with within would you your
work working team role job candidate required requirements responsibilities skills ability strong good
experience years year plus including etc looking company""".split())


def _has(text, term):
    return re.search(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])", text.lower()) is not None


def extract_skills(text):
    """Return the set of canonical skills (from SKILLS) mentioned in the text."""
    found = set()
    for skill, aliases in SKILLS.items():
        if any(_has(text, t) for t in (skill,) + tuple(aliases)):
            found.add(skill)
    return found


def _tokens(text):
    return [t.strip(".-") for t in re.findall(r"[a-z][a-z+#.\-]{3,}", text.lower())]


def score_resume(resume_text, jd_text):
    """Compare resume and job description; return a dict with score, breakdown and keyword lists."""
    if not resume_text.strip() or not jd_text.strip():
        raise ValueError("Resume and job description must both be non-empty.")
    r_sk, j_sk = extract_skills(resume_text), extract_skills(jd_text)
    matching = sorted(j_sk & r_sk)
    partial, missing = [], []
    for s in sorted(j_sk - r_sk):
        related = any(s in g and (g & r_sk) for g in GROUPS)
        (partial if related else missing).append(s)
    notes = []
    if j_sk:
        skill_pts = 50 * (len(matching) + 0.5 * len(partial)) / len(j_sk)
    else:
        skill_pts = 25
        notes.append("No known technical skills detected in the job description; skill score set to neutral.")

    r_tokens = set(_tokens(resume_text))
    jd_top = [w for w, _ in Counter(t for t in _tokens(jd_text) if t not in STOP).most_common(25)]
    kw_hit = [w for w in jd_top if w in r_tokens]
    kw_pts = 20 * len(kw_hit) / len(jd_top) if jd_top else 10
    recommended = [w for w in jd_top if w not in r_tokens][:10]

    first_line = next((ln for ln in jd_text.splitlines() if ln.strip()), "")
    title_words = {t for t in _tokens(first_line) if t not in STOP}
    role_pts = 10 * len(title_words & r_tokens) / len(title_words) if title_words else 5

    needs_edu = any(_has(jd_text, t) for t in EDU_TERMS)
    has_edu = any(_has(resume_text, t) for t in EDU_TERMS)
    edu_pts = 10 if (not needs_edu or has_edu) else 0
    exp_pts = 10 * min(1, sum(_has(resume_text, t) for t in EXP_TERMS) / 3)

    breakdown = {
        "Required skills": (round(skill_pts, 1), 50), "Technical keywords": (round(kw_pts, 1), 20),
        "Role / title relevance": (round(role_pts, 1), 10), "Education": (round(edu_pts, 1), 10),
        "Experience & responsibilities": (round(exp_pts, 1), 10),
    }
    return {
        "overall": round(sum(v[0] for v in breakdown.values())), "breakdown": breakdown,
        "matching": matching, "partial": partial, "missing": missing,
        "recommended": recommended, "notes": notes,
    }
