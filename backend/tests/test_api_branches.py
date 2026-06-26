def test_create_and_list_branches(client, auth_headers):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Downtown"

    response = client.get("/branches", headers=auth_headers)
    assert response.status_code == 200
    branches = response.json()
    assert len(branches) == 1
    assert branches[0]["name"] == "Downtown"


def test_branches_requires_auth(client):
    response = client.get("/branches")
    assert response.status_code == 401
