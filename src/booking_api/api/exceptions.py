"""Map domain errors to HTTP responses in one place.

Response bodies match the task statement exactly:
``{"detail": "Booking not found"}`` and ``{"detail": "Slot is already booked"}``.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from booking_api.domain.errors import BookingNotFoundError, SlotAlreadyBookedError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BookingNotFoundError)
    async def handle_not_found(request: Request, exc: BookingNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Booking not found"})

    @app.exception_handler(SlotAlreadyBookedError)
    async def handle_slot_conflict(request: Request, exc: SlotAlreadyBookedError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Slot is already booked"})
