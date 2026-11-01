import sys, os, unittest, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from resume_parser import *
import docx
class Regression(unittest.TestCase):
    def test_BUG01_empty_text(self):
        self.assertEqual(parse_resume("")["name"], "Unknown")
        self.assertEqual(parse_resume("  \n ")["skills"], [])
    def test_BUG02_age_not_experience(self):
        self.assertEqual(parse_resume("Asha\nAge: 22 years\nPython")["experience"], 0)
        self.assertEqual(parse_resume("Asha\n22 years old\n3 years experience")["experience"], 3)
    def test_BUG04_phone_in_long_number(self):
        self.assertEqual(parse_resume("A\nID 123456789012345")["phone"], "")
        self.assertEqual(parse_resume("A\n+91 9876543210")["phone"], "+91 9876543210")
    def test_BUG05_generic_heading_name(self):
        self.assertEqual(parse_resume("RESUME\nRahul Sharma\nPython")["name"], "Rahul Sharma")
    def test_BUG06_docx_table_skills(self):
        p = os.path.join(tempfile.mkdtemp(), "t.docx"); d = docx.Document(); d.add_paragraph("Neha Verma")
        t = d.add_table(rows=1, cols=2); t.cell(0,0).text = "Skills"; t.cell(0,1).text = "Python, Flask, SQL"; d.save(p)
        self.assertEqual(set(parse_resume(extract_text(p))["skills"]), {"python","flask","sql"})
    def test_BUG07_unique_filenames(self):
        a, b = unique_filename("बायोडाटा.pdf"), unique_filename("बायोडाटा.pdf")
        self.assertNotEqual(a, b); self.assertTrue(a.endswith(".pdf"))
        self.assertNotIn("..", unique_filename("../../etc/passwd.pdf"))
if __name__ == "__main__": unittest.main(verbosity=2)
