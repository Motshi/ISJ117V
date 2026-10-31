# Smart CV & Career Path Recommendation Platform — Backend

Modules included: project setup, auth (FR1/FR2), CV upload (FR3), and now
**CV analysis using our own trained model** (FR4/FR5) — no external AI API.

## What's new in this version
`POST /api/cv/upload` now automatically runs the uploaded CV through our
trained Logistic Regression model (see the separate `cv-model/` project for
the EDA and training that produced it) and stores:
- `predicted_category` — the job category the model thinks this CV fits
- `confidence` — how sure the model is (0 to 1)
- `runner_up_categories` — the next 3 closest categories, useful for
  borderline CVs

The trained model files live in `app/ml/` (`cv_classifier.joblib`,
`tfidf_vectorizer.joblib`) and are loaded once when the server starts.

## Setup (same as before)
```bash
cd backend
python -m venv venv
venv\Scripts\activate          (Windows)
pip install -r requirements.txt
copy .env.example .env         (then edit .env with your real MongoDB URI)
uvicorn app.main:app --reload
```
Visit http://127.0.0.1:8000/docs

## Try it
1. Register/login (same as before) to get a token, click Authorize in /docs
2. Use `POST /api/cv/upload` with a real PDF or DOCX CV
3. The response now includes `predicted_category` and `confidence` —
   this is your trained model classifying a real CV, live

## Known limitation (be ready to explain this)
The model was trained on full-length real resumes (~750 words average).
Short or generic CV text will get lower-confidence, sometimes wrong
predictions — this isn't a bug, it's expected behaviour for a model trained
on this kind of data, and worth mentioning if asked about limitations.

## Next modules
5. Live Job Listings Retrieval (Adzuna API)
6. AI-Based CV–Job Compatibility Scoring (using this model's output)
7. Automated Application Submission
8. Application Tracking & Status Updates
9. Skill Gap Identification & Learning Recommendations
