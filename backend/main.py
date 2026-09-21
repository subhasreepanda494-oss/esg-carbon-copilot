from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.upload import router as upload_router
from backend.api.emissions import router as emissions_router
from backend.api.audit import router as audit_router

from backend.database import init_db


app = FastAPI(
    title="ESG Carbon Compliance Copilot",
    description="AI-powered ESG carbon accounting and compliance copilot",
    version="1.0.0"
)


# Initialize database
init_db()


# API routes
app.include_router(upload_router)
app.include_router(emissions_router)
app.include_router(audit_router)


# Serve frontend
app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)