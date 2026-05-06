import pytest

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
    data = response.json()
    assert data["detail"] == "Email address not confirmed"


def test_wrong_password_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": test_user["username"], "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid username or password"


def test_wrong_username_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "wrongusername", "password": test_user["password"]},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid username or password"


def test_validation_error_login(client):
    response = client.post(
        "/api/auth/login",
        json={"password": test_user["password"]},
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_signup(client, monkeypatch):
    from unittest.mock import Mock
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
    from unittest.mock import Mock
    monkeypatch.setattr("src.services.email.send_email", Mock())
    new_user = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}
    response = client.post("/api/auth/signup", json=new_user)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Email already in use"

def test_repeat_signup_email(client, monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setattr("src.services.email.send_email", Mock())
    new_user = {"username": "agent007", "email": "agent008@gmail.com", "password": "12345678"}
    response = client.post("/api/auth/signup", json=new_user)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Username already in use"