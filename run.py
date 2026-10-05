"""Entry point: python run.py  (or: uvicorn app.main:app --host 0.0.0.0 --port 8000)"""
import uvicorn

from app import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)
