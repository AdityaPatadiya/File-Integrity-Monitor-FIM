from fastapi import FastAPI
from src.api.routes import auth_routes
from src.api.database.connection import AuthBase, FimBase, auth_engine, fim_engine
from src.api.models import user_model, fim_models

app = FastAPI(title="File Integrity Monitoring API")

# Include authentication routes
app.include_router(auth_routes.router)

@app.on_event("startup")
def on_startup():
    """
    Automatically create all required database tables at startup.
    """
    AuthBase.metadata.create_all(bind=auth_engine)
    FimBase.metadata.create_all(bind=fim_engine)

@app.get("/")
def root():
    return {"message": "File Integrity Monitoring API is running!"}
