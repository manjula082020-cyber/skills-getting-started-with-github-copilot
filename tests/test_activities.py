"""
Test suite for activity management API endpoints.
Uses AAA (Arrange-Act-Assert) pattern for clear test structure.
"""


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test retrieving all available activities"""
        # Arrange
        # (No additional setup needed, activities are loaded from fixture)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_have_required_fields(self, client):
        """Test that activities contain all required fields"""
        # Arrange
        # (No additional setup needed)

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_show_correct_participant_count(self, client):
        """Test that participant counts are correct"""
        # Arrange
        # (No additional setup needed)

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert len(activities["Chess Club"]["participants"]) == 2
        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Gym Class"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Test successful signup for a new participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]

        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_participant_rejected(self, client):
        """Test that duplicate signups are rejected"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test signup fails for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client):
        """Test multiple students can signup for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"

        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email1}"
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email2}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email1 in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == 4


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """Test successful unregistration of existing participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test unregistration fails for non-registered participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test unregistration fails for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_then_unregister_flow(self, client):
        """Test complete flow of signing up then unregistering"""
        # Arrange
        activity_name = "Programming Class"
        email = "integration@mergington.edu"

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert - Signup successful
        assert signup_response.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
        initial_count = len(activities[activity_name]["participants"])

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert - Unregister successful
        assert unregister_response.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_prevent_double_signup_and_remove(self, client):
        """Test that duplicate signup is prevented, then successful removal"""
        # Arrange
        activity_name = "Gym Class"
        email = "test@mergington.edu"

        # Act & Assert - First signup succeeds
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response1.status_code == 200

        # Act & Assert - Duplicate signup fails
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response2.status_code == 400

        # Act & Assert - Removal succeeds
        response3 = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response3.status_code == 200

        # Act & Assert - Can now signup again
        response4 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response4.status_code == 200
