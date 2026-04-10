import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    """Reset activities to initial state before each test"""
    initial_activities = copy.deepcopy(app_module.activities)
    app_module.activities = initial_activities
    yield TestClient(app_module.app, follow_redirects=False)
    # Reset after test if needed, but deepcopy already does


def test_get_activities(client):
    """Test GET /activities returns all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Verify structure
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


def test_signup_success(client):
    """Test successful signup for an activity"""
    email = "newstudent@test.com"
    activity = "Chess Club"
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    assert f"Signed up {email} for {activity}" in response.json()["message"]

    # Verify added to participants
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=test@test.com")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_already_signed_up(client):
    """Test signup when student is already signed up"""
    email = "duplicate@test.com"
    activity = "Chess Club"
    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")
    # Second signup
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400
    assert "Student is already signed up" in response.json()["detail"]


def test_unregister_success(client):
    """Test successful unregister from an activity"""
    email = "unreg@test.com"
    activity = "Chess Club"
    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")
    # Then unregister
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    assert f"Unregistered {email} from {activity}" in response.json()["message"]

    # Verify removed from participants
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.post("/activities/NonExistent/unregister?email=test@test.com")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_not_signed_up(client):
    """Test unregister when student is not signed up"""
    email = "notsigned@test.com"
    activity = "Chess Club"
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400
    assert "Student is not signed up" in response.json()["detail"]


def test_root_redirect(client):
    """Test root endpoint redirects to static index"""
    response = client.get("/")
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"