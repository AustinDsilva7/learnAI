"""
Test suite for the Mergington High School Activities API

Tests all endpoints including:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/remove
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activities_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up test@mergington.edu for Chess Club"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        # First signup
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Second signup (should fail)
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_multiple_students(self, client):
        """Test multiple students can sign up for the same activity"""
        # First student
        response1 = client.post(
            "/activities/Programming Class/signup?email=student1@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second student
        response2 = client.post(
            "/activities/Programming Class/signup?email=student2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "student1@mergington.edu" in activities_data["Programming Class"]["participants"]
        assert "student2@mergington.edu" in activities_data["Programming Class"]["participants"]


class TestRemoveFromActivity:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""
    
    def test_remove_success(self, client):
        """Test successful removal of a participant"""
        # Verify participant exists
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        
        # Remove participant
        response = client.delete(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_remove_not_signed_up(self, client):
        """Test removing a student who is not signed up"""
        response = client.delete(
            "/activities/Chess Club/remove?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_remove_nonexistent_activity(self, client):
        """Test removing from an activity that doesn't exist"""
        response = client.delete(
            "/activities/NonExistent Club/remove?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_all_participants(self, client):
        """Test removing all participants from an activity"""
        activity_name = "Gym Class"
        participants = activities[activity_name]["participants"].copy()
        
        for email in participants:
            response = client.delete(
                f"/activities/{activity_name}/remove?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all participants were removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data[activity_name]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test the complete workflow of signing up and then removing"""
        email = "workflow@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity}/remove?email={email}"
        )
        assert remove_response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
    
    def test_activity_capacity_tracking(self, client):
        """Test that we can track available spots correctly"""
        activity_name = "Chess Club"
        
        # Get initial state
        response = client.get("/activities")
        initial_participants = len(response.json()[activity_name]["participants"])
        max_participants = response.json()[activity_name]["max_participants"]
        initial_spots = max_participants - initial_participants
        
        # Add a participant
        client.post(f"/activities/{activity_name}/signup?email=new@mergington.edu")
        
        # Check updated state
        response = client.get("/activities")
        new_participants = len(response.json()[activity_name]["participants"])
        new_spots = max_participants - new_participants
        
        assert new_participants == initial_participants + 1
        assert new_spots == initial_spots - 1
