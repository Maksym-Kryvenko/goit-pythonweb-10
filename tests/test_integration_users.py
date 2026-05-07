from unittest.mock import patch, AsyncMock

from conftest import test_user
from src.database.models import User, RolesEnum


def test_get_me(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "avatar_url" in data


@patch("src.services.users.UserService.upload_avatar", new_callable=AsyncMock)
def test_update_avatar_user(mock_upload_avatar, client, get_token):
    fake_url = "http://example.com/avatar.jpg"
    mock_upload_avatar.return_value = User(
        id=1,
        username=test_user["username"],
        email=test_user["email"],
        avatar_url=fake_url,
        is_verified=True,
        role=RolesEnum.admin,
    )

    headers = {"Authorization": f"Bearer {get_token}"}
    file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

    response = client.patch("/api/users/avatar", headers=headers, files=file_data)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert data["avatar_url"] == fake_url

    mock_upload_avatar.assert_called_once()
