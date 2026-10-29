
def test_tasks_require_authentication(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401


def test_create_and_list_task(client, auth_headers):
    create_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Study Python",
            "description": "Practice FastAPI",
            "priority": "high",
            "status": "pending",
        },
    )

    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "Study Python"
    assert task["priority"] == "high"
    assert task["status"] == "pending"

    list_response = client.get(
        "/api/v1/tasks",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    assert any(item["id"] == task["id"] for item in list_response.json())


def test_complete_task(client, auth_headers):
    create_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Complete a test task"},
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_invalid_task_priority_is_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Invalid task",
            "priority": "impossible",
        },
    )

    assert response.status_code == 422


def test_task_cannot_be_accessed_without_authentication(
    client, auth_headers
):
    create_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Private task"},
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 401


def test_assistant_requires_authentication(client):
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Help me plan my day"},
    )
    assert response.status_code == 401


def test_assistant_reports_missing_ai_configuration(client, auth_headers):
    response = client.post(
        "/api/v1/assistant/chat",
        headers=auth_headers,
        json={"message": "Help me plan my day"},
    )
    assert response.status_code == 503
