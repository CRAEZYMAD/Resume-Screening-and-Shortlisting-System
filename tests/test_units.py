import sys, os, unittest, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from resume_parser import extract_skills, parse_resume, parse_jd, extract_text
from matcher import score_candidate
import docx
from reportlab.pdfgen import canvas

def make_docx(path, lines):
    d = docx.Document()
    for l in lines: d.add_paragraph(l)
    d.save(path)

def make_pdf(path, lines):
    c = canvas.Canvas(path)
    y = 800
    for l in lines:
        c.drawString(72, y, l); y -= 18
    c.save()

RESUME = ["Rahul Sharma", "rahul.sharma@example.com | +91 9876543210",
          "Skills: Python, Flask, SQL, Git, HTML, CSS",
          "Experience: 3 years as backend developer"]

class SkillExtraction(unittest.TestCase):
    def test_UT01_basic_skills(self):
        self.assertEqual(set(extract_skills("I know Python and SQL")), {"python", "sql"})
    def test_UT02_case_insensitive(self):
        self.assertIn("python", extract_skills("PYTHON developer"))
    def test_UT03_java_not_matched_in_javascript(self):
        s = extract_skills("Expert in JavaScript")
        self.assertIn("javascript", s); self.assertNotIn("java", s)
    def test_UT04_cpp_detected(self):
        self.assertIn("c++", extract_skills("Languages: C++, Python"))
    def test_UT05_multiword_skill(self):
        self.assertIn("machine learning", extract_skills("Interested in Machine Learning"))
    def test_UT06_no_skills(self):
        self.assertEqual(extract_skills("Cooking and painting"), [])
    def test_UT07_substring_not_matched(self):
        self.assertNotIn("git", extract_skills("digital marketing and gitlab"))

class ResumeParsing(unittest.TestCase):
    def test_UT08_email(self):
        self.assertEqual(parse_resume("\n".join(RESUME))["email"], "rahul.sharma@example.com")
    def test_UT09_phone_with_country_code(self):
        self.assertEqual(parse_resume("\n".join(RESUME))["phone"], "+91 9876543210")
    def test_UT10_phone_plain_10_digits(self):
        self.assertEqual(parse_resume("A B\nCall 9123456780")["phone"], "9123456780")
    def test_UT11_invalid_phone_ignored(self):
        self.assertEqual(parse_resume("A B\n1234567890")["phone"], "")
    def test_UT12_name_first_line(self):
        self.assertEqual(parse_resume("\n".join(RESUME))["name"], "Rahul Sharma")
    def test_UT13_experience_years(self):
        self.assertEqual(parse_resume("\n".join(RESUME))["experience"], 3)
    def test_UT14_experience_plus_sign(self):
        self.assertEqual(parse_resume("X\n5+ years of work")["experience"], 5)
    def test_UT15_no_experience_is_zero(self):
        self.assertEqual(parse_resume("X\nFresher")["experience"], 0)
    def test_UT16_missing_email_empty(self):
        self.assertEqual(parse_resume("X\nno contact")["email"], "")

class JDParsing(unittest.TestCase):
    def test_UT17_jd_skills_and_exp(self):
        jd = parse_jd("Need Python, SQL and Flask with 2 years experience")
        self.assertEqual(set(jd["skills"]), {"python", "sql", "flask"})
        self.assertEqual(jd["min_experience"], 2)
    def test_UT18_jd_without_experience(self):
        self.assertEqual(parse_jd("Python developer")["min_experience"], 0)

class Scoring(unittest.TestCase):
    JD = "Looking for Python, Flask, SQL developer with 2 years experience"
    def _score(self, text, jd_text=None):
        jd_text = jd_text or self.JD
        return score_candidate(text, parse_resume(text), jd_text, parse_jd(jd_text))
    def test_UT19_full_match_high(self):
        r = self._score("Amit\nPython Flask SQL developer, 3 years experience")
        self.assertEqual(r["skill_score"], 100.0); self.assertEqual(r["experience_score"], 100.0)
        self.assertGreater(r["match_score"], 80)
    def test_UT20_no_match_low(self):
        r = self._score("Sita\nChef with 5 years cooking pastry")
        self.assertEqual(r["skill_score"], 0.0); self.assertLess(r["match_score"], 25)
    def test_UT21_partial_skill_match(self):
        r = self._score("Ravi\nPython only, 2 years")
        self.assertAlmostEqual(r["skill_score"], 33.33, places=2)
        self.assertEqual(r["missing_skills"], "flask, sql")
    def test_UT22_experience_capped_at_100(self):
        self.assertEqual(self._score("A\nPython 10 years")["experience_score"], 100.0)
    def test_UT23_experience_partial(self):
        self.assertEqual(self._score("A\nPython 1 year")["experience_score"], 50.0)
    def test_UT24_score_in_range(self):
        r = self._score("A\nPython Flask SQL 3 years")
        self.assertTrue(0 <= r["match_score"] <= 100)
    def test_UT25_ranking_order(self):
        good = self._score("A\nPython Flask SQL 3 years")["match_score"]
        mid = self._score("B\nPython 1 year")["match_score"]
        bad = self._score("C\nPainter 10 years")["match_score"]
        self.assertTrue(good > mid > bad)
    def test_UT26_formula_weights(self):
        r = self._score("A\nPython Flask SQL 3 years")
        exp = 0.5*r["skill_score"] + 0.3*r["text_similarity"] + 0.2*r["experience_score"]
        self.assertAlmostEqual(r["match_score"], exp, delta=0.02)
    def test_UT27_deterministic(self):
        a = self._score("A\nPython Flask 3 years"); b = self._score("A\nPython Flask 3 years")
        self.assertEqual(a, b)
    def test_UT28_jd_no_skills_no_crash(self):
        r = self._score("A\nPython 3 years", jd_text="We need a motivated person")
        self.assertEqual(r["skill_score"], 0)

class FileExtraction(unittest.TestCase):
    def setUp(self): self.d = tempfile.mkdtemp()
    def test_IT01_docx_pipeline(self):
        p = os.path.join(self.d, "r.docx"); make_docx(p, RESUME)
        info = parse_resume(extract_text(p))
        self.assertEqual(info["name"], "Rahul Sharma"); self.assertIn("python", info["skills"])
    def test_IT02_pdf_pipeline(self):
        p = os.path.join(self.d, "r.pdf"); make_pdf(p, RESUME)
        info = parse_resume(extract_text(p))
        self.assertEqual(info["email"], "rahul.sharma@example.com"); self.assertEqual(info["experience"], 3)
    def test_IT03_pdf_and_docx_same_result(self):
        a = os.path.join(self.d, "a.pdf"); b = os.path.join(self.d, "b.docx")
        make_pdf(a, RESUME); make_docx(b, RESUME)
        self.assertEqual(set(parse_resume(extract_text(a))["skills"]), set(parse_resume(extract_text(b))["skills"]))
    def test_IT04_empty_docx_handled(self):
        p = os.path.join(self.d, "e.docx"); make_docx(p, [])
        info = parse_resume(extract_text(p))   # after BUG-01 fix: no crash
        self.assertEqual(info["name"], "Unknown")
    def test_IT05_corrupt_pdf_raises(self):
        p = os.path.join(self.d, "bad.pdf"); open(p, "wb").write(b"not a pdf")
        with self.assertRaises(Exception): extract_text(p)
    def test_IT06_corrupt_docx_raises(self):
        p = os.path.join(self.d, "bad.docx"); open(p, "wb").write(b"not a docx")
        with self.assertRaises(Exception): extract_text(p)

class Performance(unittest.TestCase):
    def test_PT01_batch_100_resumes(self):
        jd_text = "Python Flask SQL Git developer 2 years experience"; jd = parse_jd(jd_text)
        text = "\n".join(RESUME) + "\n" + ("Worked on web applications and APIs. " * 60)
        t = time.time()
        res = [score_candidate(text, parse_resume(text), jd_text, jd) for _ in range(100)]
        el = time.time() - t
        print(f"\n[PT01] 100 resumes scored in {el:.2f}s"); self.assertLess(el, 60)

if __name__ == "__main__":
    unittest.main(verbosity=2)
