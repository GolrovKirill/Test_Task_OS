"""Application entry point.

``create_app`` is a factory: tests build a fresh application per test and get
isolated in-memory state, while ``uvicorn booking_api.main:app`` serves the
production instance.
"""

from fastapi import FastAPI

from booking_api.api.exceptions import register_exception_handlers
from booking_api.api.routers.bookings import router as bookings_router
from booking_api.infrastructure.repositories import InMemoryBookingRepository

API_TITLE = "Restaurant Booking API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Тестовое задание ОСЬ · Backend Trainee. REST API бронирования столика в ресторане."
)


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION, description=API_DESCRIPTION)

    # Single shared store for the whole application lifetime.
    app.state.booking_repository = InMemoryBookingRepository()

    register_exception_handlers(app)
    app.include_router(bookings_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
