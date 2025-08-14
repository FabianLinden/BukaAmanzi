#!/usr/bin/env python3
"""
Minimal app test to identify startup issues
"""
from fastapi import FastAPI
from app.core.config import settings

def create_minimal_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    
    @app.get("/")
    async def root():
        return {"message": "Minimal app is working"}
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_minimal_app()
    print("Minimal app created successfully")
    uvicorn.run(app, host="0.0.0.0", port=8001)
