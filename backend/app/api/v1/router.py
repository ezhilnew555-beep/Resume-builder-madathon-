from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    dashboard,
    resume,
    jobs,
    reports,
    auth,
    profile,
    evidence,
    explanations,
    builder,
    learning,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(profile.router, tags=["Profile & Connections"])
api_router.include_router(evidence.router, tags=["Evidence Verification"])
api_router.include_router(resume.router, tags=["Resume Analysis"])
api_router.include_router(jobs.router, tags=["Job Matching"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(explanations.router, tags=["AI Explanations & Assistant"])
api_router.include_router(builder.router, tags=["Resume Builder & Export"])
api_router.include_router(learning.router, tags=["Personalized Learning Roadmap"])
