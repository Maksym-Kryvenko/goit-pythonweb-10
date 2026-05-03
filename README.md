# Contacts API

A REST API for contact management built with FastAPI, SQLAlchemy, and PostgreSQL.

## Requirements

- Python 3.14+
- PostgreSQL 13+
- Poetry

## Running with Docker Compose (recommended)

```bash
# 1. Copy environment file and fill in your values
cp .env.example .env

# 2. Start all services (app + postgres)
docker compose up --build

# 3. In a separate terminal, run migrations
docker compose exec web alembic upgrade head
```

The API will be available at http://localhost:8000  
Swagger docs at http://localhost:8000/docs

## Running locally (without Docker)

**1. Install dependencies**
```bash
poetry install
```

**2. Start PostgreSQL**
```bash
docker run --name contacts-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=... \
  -e POSTGRES_DB=contacts \
  -p 5432:5432 \
  -d postgres:13
```

**3. Configure environment**
```bash
cp .env.example .env
# Edit .env to match your database credentials
```

**4. Create the database** (if not using the docker run command above)
```bash
psql -U postgres -c "CREATE DATABASE contacts;"
```

**5. Run migrations**
```bash
poetry run alembic upgrade head
```

**6. Start the server**
```bash
poetry run uvicorn main:app --reload
```

The API will be available at http://localhost:8000  
Swagger docs at http://localhost:8000/docs

## API Endpoints

### Authentication

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/signup` | Create a new user account |
| POST | `/api/auth/login` | User login (returns access & refresh tokens) |
| POST | `/api/auth/refresh` | Refresh access token using refresh token |
| POST | `/api/auth/logout` | Logout user (invalidate refresh token) |
| GET | `/api/auth/confirmed_email/{token}` | Confirm email address |
| POST | `/api/auth/request_email` | Request email confirmation link |

### Users

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/users/me` | Get current authenticated user profile |
| PATCH | `/api/users/avatar` | Upload/update user avatar (Cloudinary) |

### Contacts

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/contacts/` | List all contacts (supports search & filtering) |
| GET | `/api/contacts/{id}` | Get contact by ID |
| POST | `/api/contacts/` | Create a new contact |
| PATCH | `/api/contacts/{id}` | Partially update a contact |
| DELETE | `/api/contacts/{id}` | Delete a contact |

### Utilities

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/utils/healthcheck` | Database health check |

### Query Parameters for `GET /api/contacts/`

- `q` — search by first name, last name, or email (e.g. `?q=john`)
- `upcoming_birthdays` — filter contacts with birthdays in the next 7 days (e.g. `?upcoming_birthdays=true`)
- `skip` / `limit` — pagination (default: `skip=0`, `limit=50`)

### Authentication

All endpoints except `/api/auth/signup`, `/api/auth/login`, `/api/auth/confirmed_email/{token}`, and `/api/auth/request_email` require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Rate Limiting

- `/api/users/me` — 10 requests/minute
- `/api/users/avatar` — 5 requests/minute
- `/api/contacts/*` — 10 requests/minute
