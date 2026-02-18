"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {"participants": details["participants"].copy()}
        for name, details in activities.items()
    }
    yield
    # Restore original state after test
    for name, details in activities.items():
        details["participants"] = original_activities[name]["participants"]


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data

    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")
        
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data["Basketball"]["participants"]

    def test_signup_fails_for_nonexistent_activity(self, client, reset_activities):
        """Test that signup fails for non-existent activity"""
        email = "student@mergington.edu"
        response = client.post(
            f"/activities/NonexistentActivity/signup?email={email}"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_fails_for_duplicate_email(self, client, reset_activities):
        """Test that signup fails when email is already registered"""
        email = "testduplicate@mergington.edu"
        
        # First signup should succeed
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Second signup with same email should fail
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email (properly URL encoded)"""
        from urllib.parse import quote
        email = "student+test@mergington.edu"
        encoded_email = quote(email)
        response = client.post(
            f"/activities/Basketball/signup?email={encoded_email}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data["Basketball"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregister from activity"""
        email = "student@mergington.edu"
        
        # First add the student
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        email = "student@mergington.edu"
        
        # Add and then remove student
        client.post(f"/activities/Basketball/signup?email={email}")
        client.delete(f"/activities/Basketball/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities_data = response.json()
        assert email not in activities_data["Basketball"]["participants"]

    def test_unregister_fails_for_nonexistent_activity(self, client, reset_activities):
        """Test that unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/NonexistentActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_fails_for_not_registered_student(self, client, reset_activities):
        """Test that unregister fails for student not registered"""
        email = "notstudent@mergington.edu"
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_multiple_times_fails(self, client, reset_activities):
        """Test that unregistering twice fails"""
        email = "student@mergington.edu"
        
        # Add student
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # First unregister should succeed
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Second unregister should fail
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 400


class TestRootRedirect:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
