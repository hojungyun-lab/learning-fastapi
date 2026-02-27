# tests/test_auth.py — 인증 테스트


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        # password가 응답에 포함되지 않음을 확인
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, test_user):
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "password123",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "short",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post("/auth/token", data={
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/auth/token", data={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/token", data={
            "username": "nobody",
            "password": "password123",
        })
        assert response.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

    def test_me_unauthenticated(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401
