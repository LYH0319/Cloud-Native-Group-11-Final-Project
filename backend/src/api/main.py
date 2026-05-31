import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from src.api.routers import frontend
from src.api.routers import history, jobs
from src.database.connection import Base, engine

app = FastAPI(
    title="Group 11 Job Scheduler API",
    description="Current API surface for manual triggers, execution history, and worker result reporting.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    last_error: OperationalError | None = None

    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as error:
            last_error = error
            time.sleep(2)

    if last_error:
        raise last_error


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Job Scheduler System API is running"}


app.include_router(jobs.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(frontend.router, prefix="/api")
