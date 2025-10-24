from fastapi import FastAPI
from src.api.routes import auth_routes

app = FastAPI(title="FIM API")

app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"message": "File Integrity Monitoring API is running!"}
