import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a clean state for each test"""
    original_activities = {
        "Test Activity": {
            "description": "Test activity",
            "schedule": "Test time",
            "max_participants": 2,
            "participants": ["test1@example.com"]
        }
    }
    activities.clear()
    activities.update(original_activities)
    yield
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    def test_get_activities_returns_dict(self, client):
        # Arrange - No setup needed, activities already loaded
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert "Test Activity" in response.json()

    def test_activity_has_required_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activity = response.json()["Test Activity"]
        
        # Assert
        assert all(field in activity for field in expected_fields)
        assert activity["max_participants"] == 2
        assert len(activity["participants"]) == 1


class TestSignup:
    def test_signup_new_student_success(self, client):
        # Arrange
        activity_name = "Test Activity"
        new_email = "newstudent@example.com"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert new_email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity(self, client):
        # Arrange
        fake_activity = "Nonexistent Activity"
        student_email = "test@example.com"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_registration(self, client):
        # Arrange
        activity_name = "Test Activity"
        existing_email = "test1@example.com"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        # Arrange
        activity_name = "Test Activity"
        # Fill the activity to max capacity
        activities[activity_name]["participants"] = [
            "student1@example.com",
            "student2@example.com"
        ]
        new_email = "student3@example.com"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]
        assert new_email not in activities[activity_name]["participants"]


class TestUnregister:
    def test_unregister_registered_student(self, client):
        # Arrange
        activity_name = "Test Activity"
        email_to_remove = "test1@example.com"
        assert email_to_remove in activities[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email_to_remove not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        # Arrange
        fake_activity = "Nonexistent Activity"
        email = "test@example.com"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered_student(self, client):
        # Arrange
        activity_name = "Test Activity"
        unregistered_email = "notregistered@example.com"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": unregistered_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
