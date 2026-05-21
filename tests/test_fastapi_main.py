from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_main_page_is_available():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_first_page_is_available():
    response = client.get("/1.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_second_page_is_available():
    response = client.get("/2.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_generate_proposal_api():
    response = client.post(
        "/api/generate",
        json={
            "company_name": "ВятГУ",
            "prompt": "Сформировать коммерческое предложение на поставку рекламного стенда",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "redirect" in data
    assert "html_content" in data
    assert data["redirect"].startswith("/2.html?id=")


def test_generated_proposal_can_be_loaded():
    generate_response = client.post(
        "/api/generate",
        json={
            "company_name": "Республика Цвета",
            "prompt": "Коммерческое предложение на изготовление рекламной продукции",
        },
    )

    proposal_id = generate_response.json()["id"]

    response = client.get(f"/api/proposals/{proposal_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == proposal_id
    assert data["company_name"] == "Республика Цвета"
    assert "html_content" in data