import pytest
from datetime import date

from conftest import test_user


@pytest.fixture
def sample_contact_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+380991112233",
        "birthday": "1990-05-05",
    }

def test_create_contact(client, get_token, sample_contact_data):
    response = client.post(
        "/api/contacts/",
        json=sample_contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == "John"
    assert data["email"] == "john@example.com"
    assert "id" in data

def test_get_contacts(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.get("/api/contacts/", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 
    assert data[0]["first_name"] == "John"
