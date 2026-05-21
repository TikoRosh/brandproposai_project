from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_gamification_subsystem_is_mounted():
    response = client.get("/gamification/api/state")

    assert response.status_code == 200


def test_gamification_state_has_required_blocks():
    response = client.get("/gamification/api/state")

    assert response.status_code == 200

    data = response.json()

    assert "employee" in data
    assert "level" in data
    assert "level_progress" in data
    assert "proposals" in data
    assert "achievements" in data
    assert "leaderboard" in data


def test_gamification_generate_proposal_adds_points():
    response = client.post(
        "/gamification/api/proposals/generate",
        json={
            "title": "Тестовое КП",
            "company": "Тестовая компания",
            "generated_text": "Тестовый текст коммерческого предложения",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ok"] is True
    assert data["points_awarded"] == 50
    assert "proposal_id" in data


def test_gamification_reject_unknown_proposal_returns_404():
    response = client.post("/gamification/api/proposals/999999/reject")

    assert response.status_code == 404

    data = response.json()

    assert data["ok"] is False
    assert data["error"] == "Proposal not found"