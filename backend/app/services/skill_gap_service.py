"""
FR10: Skill Gap Identification & Learning Recommendations

Skills are recognised against the ESCO skills dictionary (loaded from
backend/data/skills_en.csv by skill_dictionary.py), so only real skills
are ever reported - not arbitrary words from the classifier vocabulary.

Demand is measured from the live jobs the CV was matched against: a skill
is a gap when it appears in a meaningful share of those jobs but is not
found in the CV. Nothing here is written for one profession.
"""
from collections import Counter

from app.services.skill_dictionary import extract_skills

MIN_JOBS = 3          # a skill must appear in at least this many jobs
MIN_SHARE = 0.04      # ...and in at least this share of the jobs analysed
MAX_RESULTS = 8


def find_skill_gaps(cv_text: str, matched_jobs: list[dict], top_n: "int | None" = None) -> list[dict]:
    jobs = matched_jobs[:top_n] if top_n else matched_jobs
    if not jobs:
        return []

    cv_skills = extract_skills(cv_text)

    counts = Counter()
    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        counts.update(extract_skills(job_text))

    total = len(jobs)

    # Debug output in the backend console: what was recognised where.
    print(f"[skill-gaps] CV skills recognised ({len(cv_skills)}): {sorted(cv_skills)}", flush=True)
    print(f"[skill-gaps] skills seen in {total} jobs: {counts.most_common(40)}", flush=True)
    gaps = [
        (skill, count)
        for skill, count in counts.items()
        if skill not in cv_skills and count >= MIN_JOBS and count / total >= MIN_SHARE
    ]
    gaps.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "skill": skill.title(),
            "seen_in_jobs": count,
            "share_of_jobs": round(count / total * 100),
            "jobs_analysed": total,
            "suggestion": f"Search for \"{skill}\" tutorials on freeCodeCamp, Coursera, or YouTube.",
        }
        for skill, count in gaps[:MAX_RESULTS]
    ]
