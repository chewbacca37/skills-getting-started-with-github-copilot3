from fastapi.testclient import TestClient
import pytest

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Play chess",
                "schedule": "Fridays",
                "max_participants": 12,
                "participants": ["existing@example.test"],
            }
        },
    )

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_details(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@example.test"]


def test_signup_adds_participant(client):
    # Arrange
    email = "new@example.test"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@example.test",
        email,
    ]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "existing@example.test"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == [email]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    email = "new@example.test"

    # Act
    response = client.post("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = "existing@example.test"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert client.get("/activities").json()["Chess Club"]["participants"] == []


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    email = "existing@example.test"

    # Act
    response = client.delete("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_nonparticipant(client):
    # Arrange
    email = "missing@example.test"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@example.test"
    ]