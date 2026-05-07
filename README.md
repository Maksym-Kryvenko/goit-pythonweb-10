# Contacts API

A REST API for contact management built with FastAPI, SQLAlchemy, and PostgreSQL.

## Requirements

- Python 3.14+
- PostgreSQL 13+
- Docker & Docker Compose (recommended)
- Poetry (for local development without Docker)

## Running the Application

By default, the `docker-compose.yml` file is configured to run the application (Web + Redis) and expects an **external/cloud PostgreSQL database**. 

### 1. Environment Setup
Copy the example environment file and fill in your actual database credentials:
```bash
cp .env.example .env
```
*Make sure to set `POSTGRESQL_HOST`, `POSTGRESQL_USER`, and `POSTGRESQL_PASSWORD` to point to your working database.*

### 2. Start Services
```bash
docker compose up --build -d
```


The API will be available at http://localhost:8000  
Swagger docs at http://localhost:8000/docs

---

## Local Development (with Local Database)

If you don't have a cloud database and want to run PostgreSQL locally inside Docker, update your `docker-compose.yml` by adding the following service and volume:

```yaml
services:
  # ... existing web and redis services ...
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: ${POSTGRESQL_USER}
      POSTGRES_PASSWORD: ${POSTGRESQL_PASSWORD}
      POSTGRES_DB: ${POSTGRESQL_DB}
    ports:
      - "${POSTGRESQL_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```
*Don't forget to set `POSTGRESQL_HOST=db` in your `.env` file if you use this approach.*

---

## Testing

The project includes both unit and integration tests. To run them locally using Poetry:

```bash
# Install dependencies
poetry install

# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=.
```

---

## Documentation

Code documentation is generated using Sphinx. To build the HTML documentation:

```bash
cd docs
make html
```
You can then open `docs/_build/html/index.html` in your browser.

---

## CI/CD

This project uses **GitHub Actions** for automated workflows:
- **Continuous Integration (CI):** Automatically runs formatting checks and the test suite on every Push/Pull Request.
- **Continuous Deployment (CD):** Automatically deploys the application to the production server upon successful merges into the `main` branch.

---

## API Endpoints

### Authentication

All endpoints except `/api/auth/signup`, `/api/auth/login`, `/api/auth/confirmed_email/{token}`, `/api/auth/request_email`, `/api/auth/request-password-reset`, and `/api/auth/reset-password` require a valid JWT access token in the `Authorization` header:
`Authorization: Bearer <access_token>`

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/signup` | Create a new user account |
| POST | `/api/auth/login` | User login (returns access & refresh tokens) |
| POST | `/api/auth/refresh` | Refresh access token using refresh token |
| POST | `/api/auth/logout` | Logout user (invalidate refresh token) |
| GET | `/api/auth/confirmed_email/{token}` | Confirm email address |
| POST | `/api/auth/request_email` | Request email confirmation link |
| POST | `/api/auth/request-password-reset` | Send a password-reset email with a token |
| POST | `/api/auth/reset-password` | Validate reset token and update password |

#### Login details
- **Endpoint**: `POST /api/auth/login`                                                  
- **Body**: JSON                      
```json                                                                                 
{                                                                                     
  "username": "your_username",
  "password": "your_password"
}                                                                                       
```
*⚠️ Deprecated: form-data (`application/x-www-form-urlencoded`) is no longer supported.*

### Users

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/users/me` | Get current authenticated user profile |
| PATCH | `/api/users/avatar` | Upload/update user avatar (Cloudinary) |

### Contacts

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/contacts/` | List all contacts (supports search & filtering) |
| GET | `/api/contacts/{contact_id}` | Get contact by ID |
| POST | `/api/contacts/` | Create a new contact |
| PATCH | `/api/contacts/{contact_id}` | Partially update a contact |
| DELETE | `/api/contacts/{contact_id}` | Delete a contact |

#### Query Parameters for `GET /api/contacts/`
- `q` — search by first name, last name, or email (e.g. `?q=john`)
- `upcoming_birthdays` — filter contacts with birthdays in the next 7 days (e.g. `?upcoming_birthdays=true`)
- `skip` / `limit` — pagination (default: `skip=0`, `limit=50`)

### Utilities

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/utils/healthcheck` | Database health check |

---

## Rate Limiting
To prevent abuse, the following rate limits are applied:
- `/api/auth/signup` — 3 requests/minute
- `/api/auth/login`, `/api/auth/refresh` — 5 requests/minute
- `/api/auth/request-password-reset`, `/api/auth/reset-password` — 1 request/minute
- `/api/users/me` — 10 requests/minute
- `/api/users/avatar` — 5 requests/minute
- `/api/contacts/*` — 10 requests/minute
```