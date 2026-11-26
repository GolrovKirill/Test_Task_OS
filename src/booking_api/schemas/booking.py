"""Pydantic v2 schemas for the bookings API.

Field-level rules (name length, phone format, guests range) are declared with
``Field`` constraints and cross-field business rules (date window, whole-hour
slots) with validators, so every violation produces FastAPI's standard 422
response with a machine-readable ``detail``.
"""

from datetime import date, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = r"^\+7\d{10}$"

# The table can be booked no more than this many days ahead (today excluded).
MAX_DAYS_AHEAD = 30
# The restaurant takes reservations on whole hours only, from 12:00 to 22:00.
FIRST_BOOKING_HOUR = 12
LAST_BOOKING_HOUR = 22


class BookingCreate(BaseModel):
    """Payload of ``POST /bookings``."""

    name: str = Field(min_length=2, max_length=50, description="Имя гостя, 2–50 символов")
    phone: str = Field(pattern=PHONE_PATTERN, description="Номер в формате +7XXXXXXXXXX")
    booking_date: date = Field(description="Дата брони (сегодня + до 30 дней вперёд)")
    booking_time: time = Field(description="Целый час с 12:00 до 22:00")
    guests: int = Field(ge=1, le=10, description="Количество гостей, 1–10")

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, value: date) -> date:
        today = date.today()
        if value < today:
            raise ValueError("booking_date must not be in the past")
        if value > today + timedelta(days=MAX_DAYS_AHEAD):
            raise ValueError(f"booking_date must be within {MAX_DAYS_AHEAD} days from today")
        return value

    @field_validator("booking_time")
    @classmethod
    def validate_booking_time(cls, value: time) -> time:
        if (value.minute, value.second) != (0, 0):
            raise ValueError("booking_time must be a whole hour, e.g. 18:00")
        if not FIRST_BOOKING_HOUR <= value.hour <= LAST_BOOKING_HOUR:
            raise ValueError(
                f"booking_time must be between {FIRST_BOOKING_HOUR}:00 and {LAST_BOOKING_HOUR}:00"
            )
        return value


class BookingOut(BaseModel):
    """Booking as returned by every endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int
    status: Literal["active", "cancelled"]
