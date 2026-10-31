"""
FR6: Live Job Listings Retrieval

Pulls real, current job postings from the Adzuna Job API (free tier).
This is a data-retrieval integration only — no AI/model logic lives here;
that happens separately once we have both a CV analysis result and a set
of live jobs to compare it against (Module 7 — matching).

Adzuna docs: https://developer.adzuna.com/docs/search
"""
import httpx
import asyncio
from app.core.config import settings

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


async def search_jobs(keywords: str, location: str = "", results_per_page: int = 20, page: int = 1) -> list[dict]:
    """
    Search Adzuna for live job listings matching a keyword (e.g. a predicted
    CV category like 'Information Technology') and optional location.
    """
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise ValueError(
            "Adzuna credentials are not set. Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your .env file."
        )

    country = settings.adzuna_country
    url = f"{BASE_URL}/{country}/search/{page}"

    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": results_per_page,
        "what": keywords,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    jobs = []
    for item in data.get("results", []):
        jobs.append({
            "id": str(item.get("id")),
            "title": item.get("title", ""),
            "company": (item.get("company") or {}).get("display_name", "Unknown"),
            "location": (item.get("location") or {}).get("display_name", ""),
            "description": item.get("description", ""),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "url": item.get("redirect_url", ""),
            "posted_date": item.get("created"),
        })
    return jobs


async def search_jobs_pages(keywords: str, location: str = "", pages: int = 3, results_per_page: int = 50) -> list[dict]:
    """Several result pages fetched at the same time and combined (duplicates
    removed). Adzuna only returns a short snippet per job, so skill-gap
    analysis needs more jobs to be reliable."""
    results = await asyncio.gather(
        *[search_jobs(keywords, location, results_per_page, p) for p in range(1, pages + 1)],
        return_exceptions=True,
    )
    if isinstance(results[0], Exception):
        raise results[0]          # page 1 failed: report the error
    jobs, seen = [], set()
    for batch in results:
        if isinstance(batch, Exception) or not batch:
            continue              # a later page failed or was empty: skip it
        for job in batch:
            if job["id"] not in seen:
                seen.add(job["id"])
                jobs.append(job)
    return jobs
