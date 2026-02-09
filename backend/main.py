"""
FastAPI application entry point
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import uvicorn

app = FastAPI(
    title="Merton Credit Signal Generator API",
    description="Real-time credit arbitrage signals using the Merton structural model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
origins = [
    "http://localhost:3000",
    "https://merton-signals.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "message": "Merton Credit Signal Generator API",
        "docs": "/docs",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)