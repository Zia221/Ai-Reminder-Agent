
from datetime import datetime
from zoneinfo import ZoneInfo


def test_progress_requires_auth(client):
    response = client.get("/api/v1/progress/daily")
    assert response.status_code == 401


def test_daily_goal_can_be_created_and_updated(client, auth_headers):
    today = datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()

    first = client.put(
        "/api/v1/progress/goal",
        headers=auth_headers,
        json={"goal_date": today, "target_tasks": 5},
    )
    assert first.status_code == 200
    assert first.json()["target_tasks"] == 5

    second = client.put(
        "/api/v1/progress/goal",
        headers=auth_headers,
        json={"goal_date": today, "target_tasks": 7},
    )
    assert second.status_code == 200
    assert second.json()["target_tasks"] == 7

    daily = client.get(
        f"/api/v1/progress/daily?day={today}&timezone=Asia%2FKarachi",
        headers=auth_headers,
    )
    assert daily.status_code == 200
    assert daily.json()["goal_target"] == 7


def test_progress_history_returns_requested_number_of_days(
    client, auth_headers
):
    response = client.get(
        "/api/v1/progress/history?days=7",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()["days"]) == 7


def test_goal_rejects_invalid_target(client, auth_headers):
    today = datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()

    response = client.put(
        "/api/v1/progress/goal",
        headers=auth_headers,
        json={"goal_date": today, "target_tasks": 0},
    )

    assert response.status_code == 422
