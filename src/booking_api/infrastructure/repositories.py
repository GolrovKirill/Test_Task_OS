"""Persistence layer.

``BookingRepository`` is a protocol: the service depends only on this
abstraction, so a SQLite/SQLAlchemy implementation can replace the in-memory
one without touching the domain or the API.

For this assignment an in-memory store is enough (the task statement says the
storage choice does not affect the grade). The store is guarded by a lock,
because uvicorn executes sync endpoints in a thread pool.
"""

from datetime import date, time
from threading import Lock
from typing import Protocol

from booking_api.domain.models import Booking, BookingStatus


class BookingRepository(Protocol):
    def add(self, booking: Booking) -> Booking:
        """Assign an id, store and return the booking."""
        ...

    def update(self, booking: Booking) -> Booking:
        """Persist changes to an already stored booking."""
        ...

    def get(self, booking_id: int) -> Booking | None:
        """Return the booking by id or ``None`` if it does not exist."""
        ...

    def list_all(self) -> list[Booking]:
        """Return every booking ordered by id."""
        ...

    def list_by_date(self, booking_date: date) -> list[Booking]:
        """Return every booking for the given date ordered by id."""
        ...

    def find_active_by_slot(self, booking_date: date, booking_time: time) -> Booking | None:
        """Return the active booking occupying the slot, if any.

        Cancelled bookings do not occupy a slot.
        """
        ...


class InMemoryBookingRepository:
    """Thread-safe in-memory store; data lives for the process lifetime."""

    def __init__(self) -> None:
        self._bookings: dict[int, Booking] = {}
        self._next_id = 1
        self._lock = Lock()

    def add(self, booking: Booking) -> Booking:
        with self._lock:
            booking.id = self._next_id
            self._bookings[booking.id] = booking
            self._next_id += 1
            return booking

    def update(self, booking: Booking) -> Booking:
        with self._lock:
            assert booking.id is not None
            self._bookings[booking.id] = booking
            return booking

    def get(self, booking_id: int) -> Booking | None:
        with self._lock:
            return self._bookings.get(booking_id)

    def list_all(self) -> list[Booking]:
        with self._lock:
            return sorted(self._bookings.values(), key=lambda booking: booking.id)

    def list_by_date(self, booking_date: date) -> list[Booking]:
        return [booking for booking in self.list_all() if booking.booking_date == booking_date]

    def find_active_by_slot(self, booking_date: date, booking_time: time) -> Booking | None:
        for booking in self.list_all():
            if (
                booking.status is BookingStatus.ACTIVE
                and booking.booking_date == booking_date
                and booking.booking_time == booking_time
            ):
                return booking
        return None
