# Resume Shortlisting Tool
Flask web app that scores resumes (PDF/DOCX) against a job description and shows a ranked shortlist.
Score = 50% skill match + 30% TF-IDF similarity + 20% experience match.

## Run
    python -m venv venv
    venv\Scripts\activate        (Windows)   |   source venv/bin/activate   (Mac/Linux)
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000
