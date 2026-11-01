import csv
import io
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, abort
from werkzeug.utils import secure_filename

import database as db
from resume_parser import extract_text, parse_resume, parse_jd
from matcher import score_candidate

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
db.init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    jd_text = request.form["job_description"]
    jd = parse_jd(jd_text)
    job_id = db.save_job(request.form["job_title"], jd_text, jd)

    for f in request.files.getlist("resumes"):
        if not f.filename.lower().endswith((".pdf", ".docx")):
            continue  # skip unsupported files
        path = os.path.join(UPLOAD_DIR, secure_filename(f.filename))
        f.save(path)
        try:
            text = extract_text(path)
            info = parse_resume(text)
            db.save_candidate(job_id, f.filename, text, info,
                              score_candidate(text, info, jd_text, jd))
        except Exception as e:  # bad file: skip, don't crash
            print("Skipped", f.filename, e)
        finally:
            if os.path.exists(path):
                os.remove(path)  # don't keep candidate files on disk

    db.assign_ranks(job_id)
    return redirect(url_for("results", job_id=job_id))


@app.route("/results/<int:job_id>")
def results(job_id):
    job = db.get_job(job_id)~
    if job is None:
        abort(404)
    top_n = request.args.get("top", 10, type=int)
    rows = db.get_results(job_id)
    return render_template("results.html", job=job, rows=rows, top_n=top_n)


@app.route("/api/candidate/<int:candidate_id>")
def candidate_api(candidate_id):
    row = db.get_candidate(candidate_id)
    if row is None:
        abort(404)
    return jsonify(dict(row))


@app.route("/export/<int:job_id>")
def export(job_id):
    top_n = request.args.get("top", 10, type=int)
    rows = db.get_results(job_id)[:top_n]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Name", "Email", "Phone", "Experience (yrs)", "Match Score",
                "Matched Skills", "Missing Skills"])
    for r in rows:
        w.writerow([r["rank_position"], r["name"], r["email"], r["phone"],
                    r["experience_years"], r["match_score"], r["matched_skills"], r["missing_skills"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=shortlist_{job_id}.csv"})


if __name__ == "__main__":
    app.run(debug=True)
