# HomeServe

HomeServe is a full-stack household-service booking platform built as a final-year placement and internship project. It connects customers with approved service professionals and provides separate workflows for customers, professionals, and administrators.

## Tech stack

- **Frontend:** Vue 3, Vue Router, Vite, CSS
- **Backend:** Python, Flask, SQLAlchemy, Flask-Migrate, JWT authentication
- **Database:** PostgreSQL
- **Background jobs:** Celery, Celery Beat, Redis
- **Testing:** Python `unittest`

## Main features

### Customers

- Register and log in using JWT authentication
- Browse real services and prices managed by the administrator
- Detect and validate a booking location against supported cities and states
- Create and cancel eligible bookings
- Follow booking status from request through completion
- Open the service address in Google Maps
- Complete a demo payment flow
- Rate and review completed work
- Download PDF invoices

### Professionals

- Register for a service category and wait for administrator approval
- Detect a GPS-based active work city at every approved professional login
- View matching available jobs
- Accept one active job at a time
- Update jobs through accepted and completed states
- View customer directions in Google Maps
- View today's earnings and custom weekly earnings summaries
- Receive scheduled job reminders

### Administrators

- Review, approve, block, and unblock professionals
- Manage services, descriptions, and prices
- Manage supported city-and-state service areas
- View Top 5 city demand analytics
- Monitor customers and service requests
- View platform commission revenue
- Export revenue data as CSV

### Background processing

- Booking confirmation emails
- Booking completion emails
- One-hour professional reminders using Celery Beat
- Redis-backed Celery task queue

## Project structure

```text
backend/
  app/
    admin/          Administrator API routes
    auth/           Authentication routes and role protection
    customer/       Customer API routes
    professional/   Professional API routes
    templates/      Email templates
    config.py       Environment-based configuration
    models.py       SQLAlchemy database models
    tasks.py        Celery background tasks
  migrations/       PostgreSQL schema history
  tests/            Backend test suite
  make_celery.py    Celery entry point
  run.py            Flask development entry point
frontend/
  src/
    components/     Shared role-specific headers
    pages/          Vue pages
    router/         Frontend routes
    styles/         Global and section-specific styles
```

## Local setup

### 1. PostgreSQL and environment variables

Create a PostgreSQL database named `homeserve`. Copy `.env.example` to `.env` and replace every placeholder value.

Never commit `.env`; it contains database, JWT, administrator, and email credentials.

### 2. Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
flask --app app:create_app db upgrade
python run.py
```

The API runs at `http://127.0.0.1:5000`.

### 3. Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vue application runs at `http://localhost:5173`. Vite proxies `/api` requests to Flask during development.

### 4. Redis and Celery

Start Redis with Docker Desktop:

```powershell
docker run --name homeserve-redis -p 6379:6379 -d redis:7-alpine
```

Then open two terminals in the `backend` directory:

```powershell
# Executes queued jobs. The solo pool is reliable on Windows.
..\.venv\Scripts\celery.exe -A make_celery worker --loglevel INFO --pool solo
```

```powershell
# Runs scheduled reminder checks. Only one Beat process should run.
..\.venv\Scripts\celery.exe -A make_celery beat --loglevel INFO
```

## Database migrations

After changing a SQLAlchemy model:

```powershell
cd backend
flask --app app:create_app db migrate -m "describe the database change"
flask --app app:create_app db upgrade
```

`migrate` creates a migration file. `upgrade` applies that migration to PostgreSQL.

## Verification

Run backend tests from the `backend` directory:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Build the frontend from the `frontend` directory:

```powershell
npm run build
```

## Railway deployment

The root `Dockerfile` builds Vue and serves it through the production Flask
application. This keeps the frontend and API on one HTTPS domain.

Create these four Railway services in one project:

1. **HomeServe Web** — connect this GitHub repository and keep the Dockerfile's default start command.
2. **Postgres** — add Railway PostgreSQL.
3. **Redis** — add Railway Redis.
4. **HomeServe Jobs** — connect the same repository and override its start command with:

```text
celery -A make_celery worker --beat --loglevel INFO
```

Keep the Jobs service at one replica so only one Beat scheduler runs.

Set these reference variables on both code services:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

Also set `JWT_SECRET_KEY`, the `ADMIN_*` values, `PLATFORM_COMMISSION_PERCENT`,
and the `MAIL_*` values from `.env.example`. Never paste the local `.env` file
into GitHub.

For the Web service, generate a public domain and configure `/api/health` as
the health-check path. PostgreSQL migrations and the idempotent administrator
seed run automatically when the Web service starts.

## Free demo deployment

The included `render.yaml` deploys the application as a free Render web
service in Singapore. Use a free Neon PostgreSQL database and paste its pooled
connection string into Render's `DATABASE_URL` prompt.

The free deployment sets `CELERY_TASK_ALWAYS_EAGER=true`, so booking-triggered
tasks run inside the web process without Redis. Render's free web service does
not provide a continuously running Celery worker, and it blocks common SMTP
ports, so scheduled reminders and Gmail delivery remain local-development
features unless paid background infrastructure or an HTTP email provider is
added later.

## Security notes

- Passwords are stored as hashes, never as plain text.
- Protected API routes require a valid JWT and the correct user role.
- Secrets are read from `.env`, which is excluded from Git.
- The included online payment screen is a demonstration flow and does not process real money.
