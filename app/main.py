from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, connections
from app.core import config
from app.db import models
from app.db.database import engine, SessionLocal
import uvicorn

# Create tables
try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Warning: Could not create database tables: {e}")

app = FastAPI(
    title=config.settings.PROJECT_NAME,
    openapi_url=f"{config.settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if config.settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in config.settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
# app.include_router(auth.router, prefix=f"{config.settings.API_V1_STR}/auth", tags=["auth"])
# app.include_router(users.router, prefix=f"{config.settings.API_V1_STR}/users", tags=["users"])
# app.include_router(connections.router, prefix=f"{config.settings.API_V1_STR}/connections", tags=["connections"])

@app.get("/")
def root():
    return {"message": "Welcome to TalentBridge API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

