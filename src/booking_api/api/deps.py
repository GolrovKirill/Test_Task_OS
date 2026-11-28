"""FastAPI dependencies: wiring the service into the routers.

The repository is created once per application and stored on ``app.state``
(see ``main.create_app``), so all requests share the same data. Each request
gets a service bound to that shared repository.
"""

from fastapi import Request

from booking_api.services.booking_service import BookingService


def get_booking_service(request: Request) -> BookingService:
    return BookingService(request.app.state.booking_repository)
