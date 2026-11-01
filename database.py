import sqlite3

DB_FILE = "resumes.db"


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            description TEXT NOT NULL, required_skills TEXT, min_experience INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL,
            name TEXT, email TEXT, phone TEXT, education TEXT, experience_years INTEGER,
            skills TEXT, file_name TEXT, resume_text TEXT,
            FOREIGN KEY (job_id) REFERENCES job_descriptions(job_id));
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL, match_score REAL, skill_score REAL, text_similarity REAL,
            experience_score REAL, matched_skills TEXT, missing_skills TEXT, rank_position INTEGER,
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
            FOREIGN KEY (job_id) REFERENCES job_descriptions(job_id));
        """)


def save_job(title, jd_text, jd):
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO job_descriptions (title, description, required_skills, min_experience) VALUES (?,?,?,?)",
            (title, jd_text, ", ".join(jd["skills"]), jd["min_experience"]))
        return cur.lastrowid


def save_candidate(job_id, filename, text, info, score):
    with get_conn() as c:
        cur = c.execute(
            """INSERT INTO candidates (job_id, name, email, phone, education,
               experience_years, skills, file_name, resume_text) VALUES (?,?,?,?,?,?,?,?,?)""",
            (job_id, info["name"], info["email"], info["phone"], info["education"],
             info["experience"], ", ".join(info["skills"]), filename, text))
        cid = cur.lastrowid
        c.execute(
            """INSERT INTO results (candidate_id, job_id, match_score, skill_score,
               text_similarity, experience_score, matched_skills, missing_skills)
               VALUES (?,?,?,?,?,?,?,?)""",
            (cid, job_id, score["match_score"], score["skill_score"], score["text_similarity"],
             score["experience_score"], score["matched_skills"], score["missing_skills"]))


def assign_ranks(job_id):
    with get_conn() as c:
        rows = c.execute("SELECT result_id FROM results WHERE job_id=? ORDER BY match_score DESC",
                         (job_id,)).fetchall()
        for rank, r in enumerate(rows, start=1):
            c.execute("UPDATE results SET rank_position=? WHERE result_id=?", (rank, r["result_id"]))


def get_job(job_id):
    with get_conn() as c:
        return c.execute("SELECT * FROM job_descriptions WHERE job_id=?", (job_id,)).fetchone()


def get_results(job_id):
    with get_conn() as c:
        return c.execute(
            """SELECT r.*, c.name, c.email, c.phone, c.education, c.experience_years, c.file_name
               FROM results r JOIN candidates c ON c.candidate_id = r.candidate_id
               WHERE r.job_id=? ORDER BY r.rank_position""", (job_id,)).fetchall()


def get_candidate(candidate_id):
    with get_conn() as c:
        return c.execute(
            """SELECT r.*, c.name, c.email, c.phone, c.education, c.experience_years, c.skills
               FROM results r JOIN candidates c ON c.candidate_id = r.candidate_id
               WHERE c.candidate_id=?""", (candidate_id,)).fetchone()
