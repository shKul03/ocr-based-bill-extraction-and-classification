from fastapi import FastAPI
from app.routes import document_routes
from app.config import settings
import logging

from app.db.database import engine
from app.db.models.document import Document

# ------------------------
# Logging Configuration
# ------------------------
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("app.main")

# ------------------------
# App Initialization
# ------------------------
app = FastAPI(title="Bill Processing Service")

app.include_router(document_routes.router)


# ------------------------
# Startup Event
# ------------------------
@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables (if not exist)")
    Document.metadata.create_all(bind=engine)


# ------------------------
# Routes
# ------------------------
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Bill Processing Service is running"}


# ------------------------
# Local Dev Runner
# ------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
