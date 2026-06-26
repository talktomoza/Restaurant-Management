def test_register_and_login(client):
    response = client.post(
        "/auth/register", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 201

    response = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "right"})
    response = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert response.status_code == 401
