def test_crud_and_persistence_in_database(client, auth):
    created = client.post("/api/messages", json={"message": "hello jane@example.com"}, auth=auth)
    assert created.status_code == 201
    data = created.json()
    assert data["message"] == "hello [REDACTED_EMAIL]"
    message_id = data["id"]

    got = client.get(f"/api/messages/{message_id}", auth=auth)
    assert got.status_code == 200
    assert got.json()["message"] == "hello [REDACTED_EMAIL]"

    listed = client.get("/api/messages", auth=auth)
    assert listed.status_code == 200
    assert any(item["id"] == message_id for item in listed.json())

    deleted = client.delete(f"/api/messages/{message_id}", auth=auth)
    assert deleted.status_code == 204
    assert client.get(f"/api/messages/{message_id}", auth=auth).status_code == 404

def test_authentication_is_required(client):
    assert client.get("/api/messages").status_code == 401
    assert client.post("/api/messages", json={"message": "hi"}).status_code == 401

def test_invalid_credentials_are_rejected(client):
    assert client.get("/api/messages", auth=("wrong", "wrong")).status_code == 401

def test_redaction_applies_before_response(client, auth):
    raw = "mail test@example.com, IP 10.0.0.1"
    response = client.post("/api/messages", json={"message": raw}, auth=auth)
    assert response.status_code == 201
    assert "test@example.com" not in response.text
    assert "10.0.0.1" not in response.text
    listed = client.get("/api/messages", auth=auth)
    assert "test@example.com" not in listed.text
    assert "10.0.0.1" not in listed.text

def test_validation_and_missing_ids(client, auth):
    assert client.post("/api/messages", json={"message": ""}, auth=auth).status_code == 422
    assert client.get("/api/messages/999", auth=auth).status_code == 404
    assert client.delete("/api/messages/999", auth=auth).status_code == 404
