"""HTTP layer for the bookings feature.

Thin by design: parsing, status codes and delegation to the service.
Business rules live in the service and in the schemas.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status

from booking_api.api.deps import get_booking_service
from booking_api.schemas.booking import BookingCreate, BookingOut
from booking_api.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    """Create a booking. 409 if the slot is already taken by an active booking."""
    return service.create(payload)


@router.get("", response_model=list[BookingOut])
def list_bookings(
    service: BookingService = Depends(get_booking_service),
    booking_date: date | None = Query(
        default=None,
        alias="date",
        description="Фильтр по дате бронирования в формате ISO, например 2026-12-15",
    ),
) -> list[BookingOut]:
    """List bookings, optionally filtered by ``?date=YYYY-MM-DD``."""
    return service.list(booking_date)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    """Return a booking by id. 404 if it does not exist."""
    return service.get(booking_id)


@router.delete("/{booking_id}", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    """Cancel a booking: the record is kept, its status becomes ``cancelled``.

    Idempotent: deleting an already cancelled booking returns 200 as well.
    """
    return service.cancel(booking_id)
