from datetime import date


def test_planning_requires_authentication(client):
    response = client.post(
        "/api/v1/planning/generate",
        json={"plan_date": date.today().isoformat(), "available_minutes": 120},
    )
    assert response.status_code == 401


def test_planner_has_deterministic_fallback_without_ai(client, auth_headers):
    created = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Prepare project demo",
            "priority": "urgent",
            "due_at": "2026-10-29T10:00:00+00:00",
        },
    )
    assert created.status_code == 201

    response = client.post(
        "/api/v1/planning/generate",
        headers=auth_headers,
        json={
            "plan_date": date.today().isoformat(),
            "available_minutes": 120,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["plan_items"]
    assert data["plan_items"][0]["title"] == "Prepare project demo"
    assert "priority" in data["summary"].lower()
    assert "openai api key" in data["summary"].lower()


def test_planning_rejects_unrealistic_available_minutes(client, auth_headers):
    response = client.post(
        "/api/v1/planning/generate",
        headers=auth_headers,
        json={
            "plan_date": date.today().isoformat(),
            "available_minutes": 1440,
        },
    )
    assert response.status_code == 422


def test_recommendation_returns_null_when_no_tasks(client, auth_headers):
    response = client.get(
        "/api/v1/planning/recommendation",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() is None
