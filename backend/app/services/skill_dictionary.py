import csv
import re
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_ESCO_PATH = _DATA_DIR / "skills_en.csv"
_SOFTWARE_PATH = _DATA_DIR / "software_skills.csv"
MAX_WORDS = 4

ALIAS_TO_SKILL: dict[str, str] = {}

# A word counts as "ordinary language" (not safe to use on its own as a skill
# name) when the trained classifier saw it in many resumes: low IDF = common.
COMMON_WORD_IDF = 3.4


def _word_is_rare(word: str) -> bool:
    """True if the word is uncommon in everyday resume/job text (data-driven,
    from the classifier's own vocabulary). Unknown words count as rare."""
    try:
        from app.services.cv_analysis_service import _vectorizer
    except Exception:
        return False  # can't tell -> be safe, don't create short aliases
    idx = _vectorizer.vocabulary_.get(word)
    return idx is None or float(_vectorizer.idf_[idx]) >= COMMON_WORD_IDF


def _clean(label: str) -> str:
    # "Python (computer programming)" -> "python"
    label = re.sub(r"\s*\(.*?\)", "", label)
    return re.sub(r"\s+", " ", label).strip().lower()


def _add(alias: str, skill: str):
    if len(alias) >= 3 and len(alias.split()) <= MAX_WORDS:
        ALIAS_TO_SKILL.setdefault(alias, skill)


def _load_esco():
    with open(_ESCO_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            skill = _clean(row["preferredLabel"])
            if not skill:
                continue
            # Skip soft/general entries (e.g. "lead others") and broad subject
            # areas (e.g. "computer technology"); keep specific, learnable skills.
            level = (row.get("reuseLevel") or "").strip().lower()
            kind = (row.get("skillType") or "").strip().lower()
            if level == "transversal" or (kind == "knowledge" and level == "cross-sector"):
                continue
            _add(skill, skill)
            for label in (row.get("altLabels") or "").split("\n"):
                raw = label.strip()
                # short ALL-CAPS acronyms are ambiguous ("ICT" means information
                # technology in job ads, not "in-circuit test"): skip them here;
                # tool acronyms such as SQL come from the O*NET file instead.
                if raw.isupper() and raw.isalpha() and len(raw) <= 5:
                    continue
                alias = _clean(label)
                # a one-word alternative name must not be an ordinary word
                # (e.g. "less", "rust", "meet") or it matches everyday text
                if " " not in alias and not _word_is_rare(alias):
                    continue
                _add(alias, skill)


def _acronym_aliases(name: str):
    """'Structured Query Language SQL' -> ('structured query language', 'sql')."""
    words = name.split()
    for i, w in enumerate(words):
        if w.isupper() and 2 <= len(w) <= 6 and w.isalpha() and i >= len(w):
            prev = words[i - len(w):i]
            if "".join(p[0] for p in prev).upper() == w:
                return " ".join(prev).lower(), w.lower()
    return None


def _load_software():
    """O*NET Software Skills: real tools/technologies (Docker, React, Excel...).
    Only technologies O*NET flags as hot or in demand are used."""
    if not _SOFTWARE_PATH.exists():
        return
    names = []
    with open(_SOFTWARE_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Hot Technology") != "Y" and row.get("In Demand") != "Y":
                continue
            name = (row.get("Workplace Example") or "").strip()
            acr = _acronym_aliases(name)
            if acr:
                full, short = acr
                _add(full, full)
                _add(short, full)
                continue
            clean = _clean(name)
            # skip generic category descriptions like "document management software"
            if not clean or re.search(r"\b(software|tools?|systems?|programs?)$", clean):
                continue
            # a one-word tool name that is also an ordinary word ("less") is skipped
            if " " not in clean and not _word_is_rare(clean):
                continue
            _add(clean, clean)
            names.append(clean)

    # "atlassian jira" is written "Jira" in job ads: also accept the last word
    # when it identifies exactly one product name (so "database" is not used).
    last_words = {}
    for n in set(names):
        parts = n.split()
        if len(parts) > 1:
            last_words.setdefault(parts[-1], set()).add(n)
    for word, owners in last_words.items():
        if len(owners) == 1 and len(word) >= 4 and word.isalpha() and _word_is_rare(word):
            _add(word, next(iter(owners)))


def _load():
    # Tools first, so a tool name wins over a look-alike ESCO phrase.
    _load_software()
    _load_esco()


_load()


def extract_skills(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+#.]+", text.lower())
    found = set()
    for n in range(1, MAX_WORDS + 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            if phrase in ALIAS_TO_SKILL:
                found.add(ALIAS_TO_SKILL[phrase])
    return found
