from fastapi import FastAPI
from app.routes import document_routes
from app.config import settings
import logging

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Bill Processing Service")

app.include_router(document_routes.router)

@app.get("/")
async def root():
    return {"message": "Bill Processing Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
