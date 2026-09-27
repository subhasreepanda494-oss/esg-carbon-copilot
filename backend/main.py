from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.upload import router as upload_router
from backend.api.emissions import router as emissions_router
from backend.api.audit import router as audit_router
from backend.api.dashboard import router as dashboard_router

from backend.database import init_db


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ESG Carbon Compliance Copilot",
    description="AI-powered ESG carbon accounting and compliance copilot",
    version="1.0.0"
)

# Add CORS middleware to prevent "Failed to fetch"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database
init_db()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# API routes
app.include_router(upload_router)
app.include_router(emissions_router)
app.include_router(audit_router)
app.include_router(dashboard_router)


# Serve frontend
app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)