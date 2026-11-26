"""Application service: business rules that tie entities and storage together.

Routes never talk to the repository directly and never implement rules —
everything goes through this service, so the HTTP layer stays thin.
"""

from datetime import date

from booking_api.domain.errors import BookingNotFoundError, SlotAlreadyBookedError
from booking_api.domain.models import Booking
from booking_api.infrastructure.repositories import BookingRepository
from booking_api.schemas.booking import BookingCreate, BookingOut


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self._repository = repository

    def create(self, data: BookingCreate) -> BookingOut:
        """Book a free slot; raise ``SlotAlreadyBookedError`` if it is taken."""
        if self._repository.find_active_by_slot(data.booking_date, data.booking_time):
            raise SlotAlreadyBookedError(data.booking_date, data.booking_time)

        booking = self._repository.add(
            Booking(
                name=data.name,
                phone=data.phone,
                booking_date=data.booking_date,
                booking_time=data.booking_time,
                guests=data.guests,
            )
        )
        return BookingOut.model_validate(booking)

    def list(self, booking_date: date | None = None) -> list[BookingOut]:
        """List bookings, optionally filtered by date."""
        bookings = (
            self._repository.list_by_date(booking_date)
            if booking_date is not None
            else self._repository.list_all()
        )
        return [BookingOut.model_validate(booking) for booking in bookings]

    def get(self, booking_id: int) -> BookingOut:
        """Return a booking; raise ``BookingNotFoundError`` if it is missing."""
        booking = self._repository.get(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        return BookingOut.model_validate(booking)

    def cancel(self, booking_id: int) -> BookingOut:
        """Cancel a booking. Idempotent: cancelling twice returns 200 both times.

        The record is kept, only its status changes to ``cancelled``.
        """
        booking = self._repository.get(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        booking.cancel()
        self._repository.update(booking)
        return BookingOut.model_validate(booking)
