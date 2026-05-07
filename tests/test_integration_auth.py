from unittest.mock import Mock

from src.services.auth import create_email_token, _create_token
from tests.conftest import test_user, unverified_user


def test_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_not_confirmed_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": unverified_user["username"], "password": unverified_user["password"]},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Email address not confirmed"


def test_wrong_password_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": test_user["username"], "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Invalid username or password"


def test_wrong_username_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "wrongusername", "password": test_user["password"]},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Invalid username or password"


def test_validation_error_login(client):
    response = client.post(
        "/api/auth/login",
        json={"password": test_user["password"]},
    )
    assert response.status_code == 422, response.text
    assert "detail" in response.json()


def test_signup(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_email", Mock())
    new_user = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}
    response = client.post("/api/auth/signup", json=new_user)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == new_user["username"]
    assert data["email"] == new_user["email"]
    assert "hashed_password" not in data
    assert "avatar_url" in data


def test_repeat_signup_email(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_email", Mock())
    new_user = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}
    response = client.post("/api/auth/signup", json=new_user)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Email already in use"


def test_repeat_signup_username(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_email", Mock())
    new_user = {"username": "agent007", "email": "agent008@gmail.com", "password": "12345678"}
    response = client.post("/api/auth/signup", json=new_user)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Username already in use"


def test_confirmed_email(client):
    token = create_email_token({"sub": unverified_user["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Email confirmed"


def test_confirmed_email_already_confirmed(client):
    token = create_email_token({"sub": test_user["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Your email is already confirmed"


def test_request_email(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_email", Mock())
    response = client.post(
        "/api/auth/request_email",
        json={"email": unverified_user["email"]},
    )
    assert response.status_code == 200, response.text
    assert "message" in response.json()


def test_refresh_token(client):
    login = client.post(
        "/api/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_logout(client):
    # Create token directly — logout only validates the JWT signature, not DB match.
    # Avoids hitting the 5/minute rate limit on /api/auth/login.
    from src.conf.config import config
    refresh_token = _create_token(
        {"sub": test_user["username"]}, config.REFRESH_TOKEN_EXPIRE_SECONDS, "refresh_token"
    )
    response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204, response.text


def test_request_password_reset(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_reset_password_email", Mock())
    response = client.post(
        "/api/auth/request-password-reset",
        json={"email": test_user["email"]},
    )
    assert response.status_code == 200, response.text
    assert "message" in response.json()


def test_reset_password(client):
    token = _create_token({"sub": test_user["email"]}, 900, "password_reset")
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Password has been reset successfully!"
