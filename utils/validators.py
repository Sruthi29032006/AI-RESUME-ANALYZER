"""Input validation helpers (no external dependencies)."""
import os

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_MB = 5
MAX_RESUME_CHARS = 20000
MAX_JD_CHARS = 8000
MIN_RESUME_CHARS = 50


def validate_file(filename, size_bytes):
    """Return (ok, message) for an uploaded file's name and size."""
    if not filename:
        return False, "No file selected."
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Upload a PDF or DOCX."
    if size_bytes == 0:
        return False, "The uploaded file is empty."
    if size_bytes > MAX_FILE_MB * 1024 * 1024:
        return False, f"File is larger than {MAX_FILE_MB} MB."
    return True, ""


def validate_job_description(text):
    """Return (ok, message) for the pasted job description."""
    if not text or not text.strip():
        return False, "Please paste a job description."
    if len(text.strip()) < 30:
        return False, "The job description is too short to analyze."
    if len(text) > MAX_JD_CHARS:
        return False, f"Job description exceeds {MAX_JD_CHARS} characters. Please shorten it."
    return True, ""


def validate_resume_text(text):
    """Return (ok, message) for extracted resume text."""
    if not text or len(text.strip()) < MIN_RESUME_CHARS:
        return False, "Little or no text was found. The file may be a scanned image or empty."
    return True, ""
