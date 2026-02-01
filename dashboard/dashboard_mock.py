from fastapi import FastAPI, Request
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.post("/dashboard")
async def receive_dashboard_data(request: Request):
    payload = await request.json()
    logging.info("📥 Dashboard received payload:")
    logging.info(payload)
    return {"status": "received"}
