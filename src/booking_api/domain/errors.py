"""Domain errors raised by the service layer.

The domain knows nothing about HTTP: the API layer maps these exceptions to
responses in one place (``api/exceptions.py``), mirroring the global exception
handler of the reference project.
"""

from datetime import date, time


class BookingError(Exception):
    """Base class for all domain errors."""


class BookingNotFoundError(BookingError):
    def __init__(self, booking_id: int) -> None:
        super().__init__(f"booking {booking_id} does not exist")
        self.booking_id = booking_id


class SlotAlreadyBookedError(BookingError):
    def __init__(self, booking_date: date, booking_time: time) -> None:
        super().__init__(f"slot {booking_date} {booking_time} is already booked")
        self.booking_date = booking_date
        self.booking_time = booking_time
