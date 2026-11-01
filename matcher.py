from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_candidate(resume_text, info, jd_text, jd):
    """Score = 50% skill match + 30% TF-IDF similarity + 20% experience match."""
    try:
        m = TfidfVectorizer(stop_words="english").fit_transform([jd_text, resume_text])
        text_sim = float(cosine_similarity(m[0], m[1])[0][0])
    except ValueError:  # empty text
        text_sim = 0.0
    matched = set(info["skills"]) & set(jd["skills"])
    skill = len(matched) / len(jd["skills"]) if jd["skills"] else 0
    need = jd["min_experience"]
    exp = min(info["experience"] / need, 1) if need else 1
    total = 0.5 * skill + 0.3 * text_sim + 0.2 * exp
    return {"match_score": round(total * 100, 2),
            "skill_score": round(skill * 100, 2),
            "text_similarity": round(text_sim * 100, 2),
            "experience_score": round(exp * 100, 2),
            "matched_skills": ", ".join(sorted(matched)),
            "missing_skills": ", ".join(sorted(set(jd["skills"]) - matched))}
