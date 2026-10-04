from app.routers.auth import router as auth_router
from app.routers.children import router as children_router
from app.routers.controls import router as controls_router
from app.routers.device_api import router as device_api_router
from app.routers.devices import router as devices_router

__all__ = ["auth_router", "children_router", "devices_router", "device_api_router", "controls_router"]
