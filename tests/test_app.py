"""
Comprehensive tests for the Mergington High School Activities API
Tests cover all endpoints with happy paths, error cases, and edge cases
"""

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_success(self):
        """Test that /activities endpoint returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_activities_have_required_fields(self):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, details in activities.items():
            assert isinstance(activity_name, str)
            assert all(field in details for field in required_fields), \
                f"Activity {activity_name} missing required fields"

    def test_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert isinstance(details["participants"], list), \
                f"Participants for {activity_name} is not a list"

    def test_max_participants_is_positive_integer(self):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert isinstance(details["max_participants"], int)
            assert details["max_participants"] > 0


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_root_redirect_follows_to_index(self):
        """Test that following redirect leads to index.html"""
        response = client.get("/", follow_redirects=True)
        # Static files return 200, not the redirect
        assert response.status_code == 200


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]

    def test_signup_adds_participant_to_activity(self):
        """Test that participant is added to activity after signup"""
        # Get initial count
        response = client.get("/activities")
        activities_before = response.json()
        count_before = len(activities_before["Programming Class"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Programming Class/signup?email=testuser@mergington.edu"
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities_after = response.json()
        count_after = len(activities_after["Programming Class"]["participants"])
        
        assert count_after == count_before + 1
        assert "testuser@mergington.edu" in activities_after["Programming Class"]["participants"]

    def test_signup_activity_not_found(self):
        """Test signup fails with 404 when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_duplicate_participant(self):
        """Test signup fails with 400 when participant already signed up"""
        # First signup
        client.post(
            "/activities/Soccer Team/signup?email=duplicate@mergington.edu"
        )
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Soccer Team/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_existing_participant_fails(self):
        """Test that existing participants cannot sign up again"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_email_parameter_encoded(self):
        """Test signup works with URL-encoded email parameters"""
        response = client.post(
            "/activities/Art%20Club/signup?email=encodetest%40mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self):
        """Test successfully unregistering an existing participant"""
        # First sign up
        client.post(
            "/activities/Drama Club/signup?email=unregister_test@mergington.edu"
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister?email=unregister_test@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_removes_participant_from_activity(self):
        """Test that participant is removed from activity after unregister"""
        email = "removal_test@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Debate Team/signup?email=" + email
        )
        
        # Verify participant is present
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Debate Team"]["participants"]
        
        # Unregister
        client.delete(
            f"/activities/Debate Team/unregister?email={email}"
        )
        
        # Verify participant is removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Debate Team"]["participants"]

    def test_unregister_activity_not_found(self):
        """Test unregister fails with 404 when activity doesn't exist"""
        response = client.delete(
            "/activities/Fake Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_participant_not_signed_up(self):
        """Test unregister fails with 400 when participant not in activity"""
        response = client.delete(
            "/activities/Basketball Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]

    def test_unregister_existing_participant_fails(self):
        """Test that unregistering someone not in the activity fails"""
        response = client.delete(
            "/activities/Science Club/unregister?email=fake@mergington.edu"
        )
        assert response.status_code == 400

    def test_unregister_activity_name_encoded(self):
        """Test unregister works with URL-encoded activity names"""
        # First, sign up to an activity with spaces in the name
        email = "encoded_test@mergington.edu"
        client.post(
            "/activities/Programming%20Class/signup?email=" + email
        )
        
        # Then unregister with encoded activity name
        response = client.delete(
            f"/activities/Programming%20Class/unregister?email={email}"
        )
        assert response.status_code == 200


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_full_signup_flow(self):
        """Test complete flow: get activities, sign up, verify in list"""
        # Get activities
        response = client.get("/activities")
        activities = response.json()
        initial_gym_count = len(activities["Gym Class"]["participants"])
        
        # Sign up
        email = "integration_test@mergington.edu"
        response = client.post(
            f"/activities/Gym%20Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant added
        response = client.get("/activities")
        activities = response.json()
        new_gym_count = len(activities["Gym Class"]["participants"])
        assert new_gym_count == initial_gym_count + 1
        assert email in activities["Gym Class"]["participants"]

    def test_signup_unregister_flow(self):
        """Test complete flow: sign up, then unregister"""
        email = "flow_test@mergington.edu"
        activity = "Science Club"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
