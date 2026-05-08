# Contacts API

A REST API for contact management built with FastAPI, SQLAlchemy, and PostgreSQL.

![CI](https://github.com/Maksym-Kryvenko/goit-pythonweb-hw-12/actions/workflows/tests.yml/badge.svg)
![CD](https://github.com/Maksym-Kryvenko/goit-pythonweb-hw-12/actions/workflows/deploy.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.14%2B-blue)

## Requirements

- Python 3.14+
- PostgreSQL 13+
- Docker & Docker Compose (recommended)
- Poetry (for local development without Docker)
- Nginx (used as a reverse proxy)

## Running the Application

By default, the `docker-compose.yml` file is configured to run the application (Web + Redis) and expects an **external/cloud PostgreSQL database**. 

### 1. Environment Setup
Copy the example environment file and fill in your actual credentials:
```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `POSTGRESQL_USER` | PostgreSQL username |
| `POSTGRESQL_PASSWORD` | PostgreSQL password |
| `POSTGRESQL_HOST` | PostgreSQL host (e.g. RDS endpoint or `db` for local Docker) |
| `POSTGRESQL_PORT` | PostgreSQL port (default: `5432`) |
| `POSTGRESQL_DB` | Database name |
| `WEB_SERVER_HOST` | Uvicorn bind host (default: `0.0.0.0`) |
| `WEB_SERVER_PORT` | Uvicorn port (default: `8000`) |
| `SECRET_KEY` | Secret key for JWT signing (generate with `openssl rand -hex 32`) |
| `ALGORITHM` | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | Access token lifetime in seconds |
| `REFRESH_TOKEN_EXPIRE_SECONDS` | Refresh token lifetime in seconds |
| `REDIS_HOST` | Redis host |
| `REDIS_PORT` | Redis port (default: `6379`) |
| `REDIS_DB` | Redis database index (default: `0`) |
| `USER_CACHE_TTL` | User profile cache TTL in seconds |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `MAIL_USERNAME` | SMTP login (e.g. Gmail address) |
| `MAIL_PASSWORD` | SMTP password (for Gmail — use an [App Password](https://myaccount.google.com/apppasswords), not your account password) |
| `MAIL_FROM` | Sender email address |
| `MAIL_PORT` | SMTP port (default: `465` for SSL) |
| `MAIL_SERVER` | SMTP server (e.g. `smtp.gmail.com`) |
| `MAIL_FROM_NAME` | Display name for outgoing emails |
| `MAIL_STARTTLS` | Use STARTTLS (`True`/`False`) |
| `MAIL_SSL_TLS` | Use SSL/TLS (`True`/`False`) |
| `USE_CREDENTIALS` | Pass credentials to SMTP (`True`/`False`) |
| `VALIDATE_CERTS` | Validate TLS certificates (`True`/`False`) |

> **Note:** Email is required for account confirmation and password reset. Configure a real SMTP provider (e.g. Gmail with App Password, SendGrid, Mailgun).

### 2. Start Services
```bash
docker compose up --build -d
```

The API will be available at http://localhost  
Swagger docs at http://localhost/docs

> Database migrations run automatically on container start via `docker-entrypoint.sh`.

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
You can then open `docs/build/html/index.html` in your browser.

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
| PATCH | `/api/users/avatar` | Upload/update user avatar to Cloudinary (**admin only**) |

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
