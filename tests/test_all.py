import io
import unittest
from unittest import mock

from utils.validators import validate_file, validate_job_description, validate_resume_text
from ats_scorer import extract_skills, score_resume
from analyzer import parse_json_response, validate_analysis, AnalyzerError, _call_gemini
from resume_parser import extract_text, ResumeParseError

RESUME = "Developed projects in Python, pandas and TensorFlow. B.Tech Computer Science. Internship experience in machine learning."
JD = "Data Scientist\nRequired: Python, SQL, PyTorch, machine learning. Bachelor degree needed."


class Tests(unittest.TestCase):
    def test_file_validation(self):
        self.assertTrue(validate_file("a.pdf", 100)[0])
        self.assertFalse(validate_file("a.txt", 100)[0])
        self.assertFalse(validate_file("a.pdf", 0)[0])
        self.assertFalse(validate_file("a.pdf", 6 * 1024 * 1024)[0])

    def test_jd_and_resume_validation(self):
        self.assertFalse(validate_job_description("")[0])
        self.assertTrue(validate_job_description("x" * 100)[0])
        self.assertFalse(validate_resume_text("hi")[0])

    def test_skill_extraction_boundaries(self):
        self.assertEqual(extract_skills("I know Javascript and C++"), {"javascript", "c++"})
        self.assertNotIn("java", extract_skills("javascript only"))

    def test_scoring(self):
        s = score_resume(RESUME, JD)
        self.assertTrue({"python", "machine learning"} <= set(s["matching"]))
        self.assertIn("pytorch", s["partial"])  # TensorFlow is a related skill
        self.assertIn("sql", s["missing"])
        self.assertTrue(0 <= s["overall"] <= 100)
        with self.assertRaises(ValueError):
            score_resume("", JD)

    def test_json_parsing_and_validation(self):
        d = parse_json_response('```json\n{"overall_assessment":"ok","strengths":["a"]}\n```')
        out = validate_analysis(d)
        self.assertEqual(out["strengths"], ["a"])
        self.assertEqual(out["bullet_improvements"], [])
        with self.assertRaises(AnalyzerError):
            parse_json_response("not json")
        with self.assertRaises(AnalyzerError):
            validate_analysis({})

    def test_missing_api_key(self):
        with mock.patch("dotenv.load_dotenv", lambda *a, **k: None), \
             mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(AnalyzerError):
                _call_gemini("hi")

    def test_parser_errors(self):
        with self.assertRaises(ResumeParseError):
            extract_text("x.txt", b"abc")
        try:
            import fitz  # noqa: F401
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        with self.assertRaises(ResumeParseError):
            extract_text("bad.pdf", b"not a pdf")

    def test_docx_roundtrip(self):
        try:
            import docx
        except ImportError:
            self.skipTest("python-docx not installed")
        d = docx.Document(); d.add_paragraph("Hello Python resume"); buf = io.BytesIO(); d.save(buf)
        self.assertIn("Hello Python", extract_text("r.docx", buf.getvalue()))
        with self.assertRaises(ResumeParseError):
            extract_text("bad.docx", b"junk")


if __name__ == "__main__":
    unittest.main()
