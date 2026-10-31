"""Extract plain text from PDF and DOCX resumes (in memory, nothing saved to disk)."""
import io
import os


class ResumeParseError(Exception):
    """Raised when a resume cannot be read."""


def _extract_pdf(data):
    import fitz  # PyMuPDF
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ResumeParseError("The PDF is corrupted or unreadable.")
    try:
        if doc.needs_pass:
            raise ResumeParseError("The PDF is password-protected. Remove the password and retry.")
        return "\n".join(page.get_text() for page in doc)
    except ResumeParseError:
        raise
    except Exception:
        raise ResumeParseError("Could not read text from this PDF.")
    finally:
        doc.close()


def _extract_docx(data):
    import docx
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception:
        raise ResumeParseError("The DOCX file is corrupted or not a valid Word document.")
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


def extract_text(filename, data):
    """Return cleaned text from a PDF/DOCX given its filename and raw bytes."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".pdf":
        text = _extract_pdf(data)
    elif ext == ".docx":
        text = _extract_docx(data)
    else:
        raise ResumeParseError("Unsupported file type. Use PDF or DOCX.")
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)
