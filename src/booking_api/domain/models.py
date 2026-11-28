"""Domain model for the bookings feature.

The entity is a plain dataclass without framework dependencies, so the
business logic in the service layer stays testable without FastAPI or
Pydantic. Identity (``id``) is assigned by the repository on ``add``.
"""

from dataclasses import dataclass
from datetime import date, time
from enum import StrEnum


class BookingStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass
class Booking:
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int
    id: int | None = None
    status: BookingStatus = BookingStatus.ACTIVE

    @property
    def slot(self) -> tuple[date, time]:
        """Unique key of a table slot: one date + one whole hour."""
        return self.booking_date, self.booking_time

    def cancel(self) -> None:
        self.status = BookingStatus.CANCELLED
