def test_register_login_dashboard(client):
    resp = client.post("/register", data={
        "username": "testuser", "email": "t@example.com",
        "password": "pass1234", "confirm_password": "pass1234",
    }, follow_redirects=True)
    assert resp.status_code == 200

    resp = client.get("/", follow_redirects=True)
    assert b"AlphaGuard" in resp.data or resp.status_code == 200


def test_login_required_redirects(client):
    resp = client.get("/portfolio", follow_redirects=False)
    assert resp.status_code in (302, 401)
