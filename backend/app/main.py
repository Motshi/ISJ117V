from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import ensure_indexes
from app.routes import auth_routes, cv_routes, jobs_routes, applications_routes

app = FastAPI(
    title="Smart CV & Career Path Recommendation Platform API",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(cv_routes.router)
app.include_router(jobs_routes.router)
app.include_router(applications_routes.router)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Smart CV Platform API is running"}
