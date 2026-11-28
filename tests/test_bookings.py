"""API tests covering the key business rules from the task statement.

Each test gets a fresh application via ``create_app``, so tests are isolated
from each other.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from booking_api.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def make_payload(**overrides: object) -> dict[str, object]:
    """Booking payload valid for tomorrow; individual fields can be overridden."""
    payload: dict[str, object] = {
        "name": "Иван Петров",
        "phone": "+71234567890",
        "booking_date": (date.today() + timedelta(days=1)).isoformat(),
        "booking_time": "18:00",
        "guests": 2,
    }
    payload.update(overrides)
    return payload


def create_booking(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/bookings", json=make_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


# --- Happy path -----------------------------------------------------------


def test_create_booking_returns_201_with_active_status(client: TestClient) -> None:
    body = create_booking(client)

    assert body["id"] == 1
    assert body["status"] == "active"
    assert body["name"] == "Иван Петров"
    assert body["phone"] == "+71234567890"


def test_get_booking_by_id(client: TestClient) -> None:
    created = create_booking(client)

    response = client.get(f"/bookings/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_list_bookings_returns_all(client: TestClient) -> None:
    create_booking(client, name="Первый")
    create_booking(client, booking_time="19:00", name="Второй")

    body = client.get("/bookings").json()

    assert [item["name"] for item in body] == ["Первый", "Второй"]


def test_list_bookings_filters_by_date(client: TestClient) -> None:
    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=2)

    create_booking(client, name="На завтра", booking_date=tomorrow.isoformat())
    create_booking(client, name="На послезавтра", booking_date=day_after.isoformat())

    response = client.get("/bookings", params={"date": tomorrow.isoformat()})

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["На завтра"]


def test_cancel_booking_keeps_record_and_sets_status(client: TestClient) -> None:
    created = create_booking(client)

    response = client.delete(f"/bookings/{created['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    # The record is kept and still readable.
    assert client.get(f"/bookings/{created['id']}").json()["status"] == "cancelled"


def test_cancelled_booking_frees_the_slot(client: TestClient) -> None:
    created = create_booking(client)
    client.delete(f"/bookings/{created['id']}")

    # The same slot can be booked again.
    assert create_booking(client)["status"] == "active"


# --- The main rule: one active booking per slot ----------------------------


def test_booking_an_occupied_slot_returns_409(client: TestClient) -> None:
    create_booking(client, name="Первый")

    response = client.post("/bookings", json=make_payload(name="Второй"))

    assert response.status_code == 409
    assert response.json() == {"detail": "Slot is already booked"}


def test_same_slot_on_another_date_is_allowed(client: TestClient) -> None:
    create_booking(client)
    day_after = date.today() + timedelta(days=2)

    response = client.post("/bookings", json=make_payload(booking_date=day_after.isoformat()))

    assert response.status_code == 201


def test_cancelled_booking_does_not_block_the_slot(client: TestClient) -> None:
    created = create_booking(client)
    client.delete(f"/bookings/{created['id']}")

    response = client.post("/bookings", json=make_payload())

    assert response.status_code == 201


# --- Errors: 404 and 422 ----------------------------------------------------


def test_get_missing_booking_returns_404(client: TestClient) -> None:
    response = client.get("/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}


def test_cancel_missing_booking_returns_404(client: TestClient) -> None:
    response = client.delete("/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}


def test_cancel_is_idempotent(client: TestClient) -> None:
    created = create_booking(client)

    first = client.delete(f"/bookings/{created['id']}")
    second = client.delete(f"/bookings/{created['id']}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "cancelled"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "Я"),  # too short
        ("name", "А" * 51),  # too long
        ("phone", "+799912345678"),  # 11 digits after +7
        ("phone", "79991234567"),  # missing +7
        ("booking_time", "18:30"),  # not a whole hour
        ("booking_time", "11:00"),  # before opening
        ("booking_time", "23:00"),  # after closing
        ("guests", 0),
        ("guests", 11),
    ],
)
def test_invalid_field_returns_422(client: TestClient, field: str, value: object) -> None:
    response = client.post("/bookings", json=make_payload(**{field: value}))

    assert response.status_code == 422


def test_past_date_returns_422(client: TestClient) -> None:
    yesterday = date.today() - timedelta(days=1)

    response = client.post("/bookings", json=make_payload(booking_date=yesterday.isoformat()))

    assert response.status_code == 422


def test_date_more_than_30_days_ahead_returns_422(client: TestClient) -> None:
    far_future = date.today() + timedelta(days=31)

    response = client.post("/bookings", json=make_payload(booking_date=far_future.isoformat()))

    assert response.status_code == 422


def test_list_with_malformed_date_returns_422(client: TestClient) -> None:
    response = client.get("/bookings", params={"date": "not-a-date"})

    assert response.status_code == 422
