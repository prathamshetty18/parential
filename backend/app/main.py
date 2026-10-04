from fastapi import FastAPI

from app.routers import (
    auth_router,
    children_router,
    controls_router,
    device_api_router,
    devices_router,
)

app = FastAPI(
    title="ROAVAI Parental Control Companion API",
    description="Parental control backend service for Wini Cloud Tutor",
    version="0.3.0",
)

app.include_router(auth_router)
app.include_router(children_router)
app.include_router(devices_router)
app.include_router(device_api_router)
app.include_router(controls_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
