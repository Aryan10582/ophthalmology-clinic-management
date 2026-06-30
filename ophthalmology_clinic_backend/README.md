# Ophthalmology Clinic Management API

Backend foundation and consultation API for a production-oriented ophthalmology clinic management system.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Pydantic v2
- JWT authentication
- Passlib/Bcrypt password hashing
- Docker and Docker Compose

## Project Structure

```text
app/
  api/              API dependencies and versioned routers
  core/             configuration, security, logging, exception handlers
  crud/             database access layer
  db/               SQLAlchemy session and metadata
  middleware/       request middleware
  models/           SQLAlchemy models
  schemas/          Pydantic request/response models
alembic/            database migration environment
```

## RBAC

- `admin`: manages users and can access all clinical endpoints.
- `doctor`: full access to patient records and visits.
- `receptionist`: can register and maintain patient demographics, but cannot manage users or clinical visit records.

Public `/auth/register` creates a receptionist account. Admins create doctors, receptionists, and other admins through `/users`.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

## Database Migrations

Create the first migration:

```bash
docker compose exec api alembic revision --autogenerate -m "initial schema"
```

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

## Initial Admin Seed

On application startup, the API creates one default administrator only when the `users` table is empty:

- Email: `admin@clinic.com`
- Password: `ClinicPass123`

You can also run the same seed manually:

```bash
docker compose exec api python -m app.cli seed-admin
```

Change this password after first login.

The dummy doctor accounts use password `Doctor@12345`:

- `rupa.kapale@clinic.com` for Dr. Rupa Kapale
- `amit.deshmukh@clinic.com` for Dr. Amit Deshmukh

The dummy receptionist accounts use password `Reception@12345`:

- `reception1@clinic.com`
- `reception2@clinic.com`

## Authentication

Login uses OAuth2 password form fields:

- `username`: user email
- `password`: user password

Important endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/users/me`

## Doctor Consultation Fields

Visits support structured refraction, optional slit lamp/fundus/general findings, intraocular pressure, and additional notes while preserving the original `prescription` and `notes` fields for backward compatibility.

## Queue, Operations, and Calendar

New Phase 2 workflow endpoints:

- `GET /api/v1/queue/today`
- `POST /api/v1/queue`
- `POST /api/v1/queue/{entry_id}/start`
- `POST /api/v1/queue/{entry_id}/complete`
- `GET /api/v1/operations`
- `POST /api/v1/operations`
- `GET /api/v1/operations/types`
- `POST /api/v1/operations/types`
- `GET /api/v1/followups`
- `GET /api/v1/calendar/events`

Apply migrations after pulling Phase 2 changes:

```bash
docker compose exec api alembic upgrade head
```

## Next Phases

Recommended next backend increments:

- Appointment scheduling
- Ophthalmic examination records
- Visual acuity and refraction models
- Billing and invoices
- Audit logging
- Test suite and CI pipeline
