import pytest
from datetime import date


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
    response = client.get(
        "/api/contacts/",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["first_name"] == "John"


def test_search_contacts(client, get_token):
    response = client.get(
        "/api/contacts/?q=John",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) > 0
    assert data[0]["first_name"] == "John"


def test_search_contacts_no_results(client, get_token):
    response = client.get(
        "/api/contacts/?q=zzznomatch",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_get_contact(client, get_token):
    response = client.get(
        "/api/contacts/1",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == 1
    assert data["first_name"] == "John"


def test_get_contact_not_found(client, get_token):
    response = client.get(
        "/api/contacts/9999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Contact not found"


def test_update_contact(client, get_token):
    response = client.patch(
        "/api/contacts/1",
        json={"last_name": "Updated"},
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["last_name"] == "Updated"


def test_update_contact_not_found(client, get_token):
    response = client.patch(
        "/api/contacts/9999",
        json={"last_name": "Ghost"},
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Contact not found"


def test_upcoming_birthdays(client, get_token):
    today = date.today()
    # Use today's month/day with year 1990 — always in the next-7-days window
    upcoming_bday = date(1990, today.month, today.day).isoformat()
    contact = {
        "first_name": "Birthday",
        "last_name": "Person",
        "email": "birthday@example.com",
        "phone_number": "+380991112244",
        "birthday": upcoming_bday,
    }
    client.post(
        "/api/contacts/",
        json=contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    response = client.get(
        "/api/contacts/?upcoming_birthdays=true",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    emails = [c["email"] for c in response.json()]
    assert "birthday@example.com" in emails


def test_delete_contact_not_found(client, get_token):
    response = client.delete(
        "/api/contacts/9999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Contact not found"


def test_delete_contact(client, get_token):
    response = client.delete(
        "/api/contacts/1",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 204, response.text

    verify = client.get(
        "/api/contacts/1",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert verify.status_code == 404
