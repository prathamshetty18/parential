from fastapi import FastAPI

app = FastAPI(
    title="ROAVAI Parental Control Companion API",
    description="Parental control backend service for Wini Cloud Tutor",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
