import re
import pdfplumber
import docx

SKILLS = ["python", "java", "c++", "sql", "html", "css", "javascript", "react",
          "flask", "django", "machine learning", "nlp", "git", "mysql", "excel"]

EDU_PATTERN = r"(b\.?\s?tech|b\.?\s?e\.?|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|bca|mca|mba|bachelor|master|diploma|ph\.?d)"


def extract_text(path):
    if path.lower().endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    return "\n".join(p.text for p in docx.Document(path).paragraphs)


def extract_skills(text):
    text = text.lower()
    return [s for s in SKILLS
            if re.search(r"(?<![a-z+#])" + re.escape(s) + r"(?![a-z+#])", text)]


def parse_resume(text):
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}", text)
    years = [int(y) for y in re.findall(r"(\d+)\+?\s*years?", text.lower())]
    edu = re.findall(EDU_PATTERN, text.lower())
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return {"name": lines[0] if lines else "Unknown",
            "email": email.group(0) if email else "",
            "phone": phone.group(0) if phone else "",
            "education": ", ".join(sorted(set(e.upper() for e in edu))),
            "experience": max(years) if years else 0,
            "skills": extract_skills(text)}


def parse_jd(jd_text):
    years = [int(y) for y in re.findall(r"(\d+)\+?\s*years?", jd_text.lower())]
    return {"skills": extract_skills(jd_text),
            "min_experience": min(years) if years else 0}
