"""
FR7: AI-Based CV–Job Compatibility Scoring

Scores how well a CV matches a job by combining two signals, both derived
directly from the CV and job text (no hand-picked keyword list, no
profession-specific hardcoding — works for any CV, in any of the 24
trained job categories):

1. Overlap with the TRAINED CLASSIFIER'S OWN VOCABULARY — the ~5,000 terms
   it learned from real resumes spanning all 24 categories.
2. General word overlap between the full CV text and the full job text —
   catches genuine matches that fall outside that specific vocabulary
   (real job-board postings are often phrased differently to resume text).

Combining both makes the score robust to either signal being sparse on its
own (which happens in practice with real, live job postings), while
staying entirely data-driven — nothing here is written for one profession
or one person's CV.
"""
import re

from app.services.cv_analysis_service import _vectorizer

_VOCABULARY = list(_vectorizer.get_feature_names_out())

# Filter out short fragments — the training data (like most PDF-scraped
# resume datasets) contains junk 2-3 letter fragments from text extraction
# artifacts, which aren't meaningful skills and were inflating match
# scores through coincidental fragment overlap. A minimum length is a
# general text-quality filter, not tied to any profession or skill list.
_VOCABULARY = [term for term in _VOCABULARY if len(term.replace(" ", "")) >= 4]

GENERIC_STOPWORDS = {
    "the", "and", "for", "are", "with", "this", "that", "from", "your",
    "you", "have", "has", "will", "our", "job", "jobs", "looking", "next",
    "talented", "role", "work", "team", "join", "apply", "please", "also",
    "including", "such", "within", "into", "about", "more", "than", "each",
}

_REQUIRED_YEARS_PATTERNS = [
    re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience", re.IGNORECASE),
    re.compile(r"minimum\s*(?:of\s*)?(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"at least\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
]
_DATE_RANGE_PATTERN = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)\d{2}|present|current)\b",
    re.IGNORECASE,
)


def _extract_required_years(job_text: str) -> "int | None":
    """Finds phrases like '5+ years experience' or 'minimum of 3 years' in a job posting."""
    for pattern in _REQUIRED_YEARS_PATTERNS:
        match = pattern.search(job_text)
        if match:
            return int(match.group(1))
    return None


def _extract_cv_experience_years(cv_text: str, current_year: int = 2026) -> "int | None":
    """
    Finds date ranges in the CV (e.g. '2019 - 2024', '2019 to Present') and
    estimates total years of experience from the earliest start to the
    latest end (or now, for 'Present'/'Current'). Returns None if the CV
    doesn't state clear date ranges — not every CV lists employment dates
    this way, and guessing would be worse than skipping this factor.
    """
    matches = _DATE_RANGE_PATTERN.findall(cv_text)
    if not matches:
        return None
    years = []
    for start_str, end_str in matches:
        start = int(start_str)
        end = current_year if end_str.lower() in ("present", "current") else int(end_str)
        years.append((start, end))
    earliest_start = min(y[0] for y in years)
    latest_end = max(y[1] for y in years)
    return max(latest_end - earliest_start, 0)


def _vocabulary_terms_present(text: str) -> set[str]:
    text_lower = text.lower()
    return {term for term in _VOCABULARY if term in text_lower}

def _general_words(text: str) -> set[str]:
    words = re.findall(r"[a-z]{4,}", text.lower())
    return set(w for w in words if w not in GENERIC_STOPWORDS)


def score_jobs_against_cv(cv_text: str, jobs: list[dict]) -> list[dict]:
    """
    Takes the raw extracted CV text and a list of job dicts (each with
    'title' and 'description' keys), and returns the same list with a
    'match_score' (0-100) added to each, sorted best-match first.

    Scored against a FIXED absolute scale, not relative to just this
    batch of jobs — otherwise, if every job in a search is genuinely a
    poor match (e.g. an HR CV searching "Software Developer"), the least
    bad one would still get stretched up to look like a strong match,
    which is actively misleading. Calibrated against real examples: a
    genuine match (HR CV vs HR job) scores ~30+ combined overlap; an
    unrelated job (HR CV vs generic dev posting) scores ~6 or less.
    """
    if not jobs:
        return jobs

    cv_vocab_terms = _vocabulary_terms_present(cv_text)
    cv_general_words = _general_words(cv_text)
    cv_experience_years = _extract_cv_experience_years(cv_text)

    COMBINED_SCORE_CEILING = 24  # combined score that counts as a "full" 98% match

    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        job_vocab_terms = _vocabulary_terms_present(job_text)
        job_general_words = _general_words(job_text)

        vocab_overlap = len(cv_vocab_terms & job_vocab_terms)
        general_overlap = len(cv_general_words & job_general_words)

        # Combined signal: vocabulary overlap counts double, since it's a
        # more targeted signal than generic word overlap.
        combined = vocab_overlap * 2 + general_overlap

        normalised = min(combined / COMBINED_SCORE_CEILING, 1.0)
        score = 10 + (normalised ** 2) * 88

        # Experience adjustment: only applied when the job actually states
        # a required number of years AND the CV states clear enough dates
        # to calculate real experience — never guessed or assumed.
        required_years = _extract_required_years(job_text)
        if required_years is not None and cv_experience_years is not None:
            if cv_experience_years >= required_years:
                score = min(score + 8, 100)  # meets/exceeds requirement — small boost
            else:
                shortfall = required_years - cv_experience_years
                score = max(score - shortfall * 10, 5)  # falls short — real penalty

        job["match_score"] = round(score)

    jobs.sort(key=lambda j: j["match_score"], reverse=True)
    return jobs
