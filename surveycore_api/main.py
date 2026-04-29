"""
SurveyCore Backend API
FastAPI REST API for multi-language survey management system.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from .routers import auth, questions, projects, surveys, public, results, admin

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SurveyCore API",
    description="Multi-language survey management system with token-based access",
    version="2.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(projects.router)
app.include_router(surveys.router)
app.include_router(public.router)
app.include_router(results.router)
app.include_router(admin.router)


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "SurveyCore API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
