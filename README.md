# Cloud-Native Group 11 Final Project

Cloud-Native Group 11 Final Project is a cloud-native job scheduling and execution platform. The system provides a web console for developers, operators, and administrators to create jobs, configure schedules, define dependencies, trigger executions, inspect run history, and monitor execution logs.

The project uses a separated frontend and backend architecture. The frontend is built with React, TypeScript, and Vite. The backend is built with FastAPI and SQLAlchemy, with MySQL for persistence, Redis for queueing, a scheduler service for cron-based dispatching, and worker services for executing jobs.

## Table of Contents

- [System Overview](#system-overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Testing](#testing)
- [Observability and Load Testing](#observability-and-load-testing)
- [Distributed Deployment](#distributed-deployment)
- [Troubleshooting](#troubleshooting)

## System Overview

The platform is designed around the lifecycle of a job:

1. A user signs in through the frontend.
2. A developer creates a REST API job or shell script job.
3. The scheduler or a manual trigger creates an execution record.
4. The execution payload is pushed into Redis.
5. A worker consumes the payload, runs the task, and reports the result.
6. The backend stores execution status, timing, worker metadata, and log references.
7. Operators and administrators review job status, execution history, metrics, and logs.

The system supports role-based access control:

| Role | Capabilities |
| --- | --- |
| Developer | Create jobs, manage owned jobs, trigger owned jobs, view owned execution history |
| Operator | View and operate all jobs, pause or resume jobs, rerun executions, inspect system execution history |
| Admin | Operator capabilities plus user account management and password reset |

## Core Features

- User authentication with JWT access tokens
- Built-in default admin account initialization
- Role-based job and execution permissions
- REST API job registration
- Shell script job registration
- Manual job triggering
- Cron-style scheduled execution
- Job dependency management with cycle detection
- Execution history filtering and detail view
- Execution log metadata and log content retrieval
- Worker result reporting and heartbeat-oriented execution tracking
- Redis-backed task queue
- Horizontally scalable worker service
- Password reset flow with optional SMTP email delivery
- Prometheus metrics endpoint
- Grafana dashboard provisioning
- k6 load test scripts
- Backend and frontend CI workflows

## Architecture

```text
Browser
  |
  v
React Frontend
  |
  v
FastAPI Backend
  |                    |
  |                    v
  |              Prometheus / Grafana
  |
  +--> MySQL
  |
  +--> Redis Queue <--> Worker Service
  |
  +--> Scheduler Service
```

Main runtime services:

| Service | Description | Default URL |
| --- | --- | --- |
| `frontend` | React and Vite web application | `http://localhost:3000` |
| `backend` | FastAPI API server | `http://localhost:8000` |
| `db` | MySQL 8.4 database | Internal Docker network |
| `redis` | Redis task queue | Internal Docker network |
| `worker` | Job execution worker | Internal Docker network |
| `scheduler` | Cron scheduler and dispatcher | Internal Docker network |
| `prometheus` | Metrics scraper | `http://localhost:9090` |
| `grafana` | Metrics dashboard | `http://localhost:3001` |
| `influxdb` | k6 time-series output database | `http://localhost:8086` |

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, Bootstrap, Vitest, Prettier |
| Backend API | FastAPI, Pydantic, SQLAlchemy |
| Database | MySQL 8.4 |
| Queue | Redis 7 |
| Worker | Python worker process with Redis queue consumption |
| Scheduler | Python cron scheduler service |
| Observability | Prometheus, Grafana, FastAPI metrics middleware |
| Load Testing | k6, InfluxDB |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Repository Structure

```text
.
|-- backend/
|   |-- config/                  # Backend settings and environment loading
|   |-- src/
|   |   |-- api/                 # FastAPI app, routers, dependencies, metrics
|   |   |-- database/            # SQLAlchemy models, schemas, CRUD helpers
|   |   |-- scheduler/           # Cron scheduler service
|   |   |-- utils/               # Security, logging, email, dependency cycle detection
|   |   `-- worker/              # Worker executor, queue manager, task runners
|   |-- tests/                   # Unit and integration tests
|   |-- Dockerfile               # Backend API image
|   |-- Dockerfile.worker        # Worker and scheduler image
|   |-- requirements.txt         # Python dependencies
|   `-- pytest.ini               # Pytest configuration
|
|-- frontend/
|   |-- public/                  # Static assets
|   |-- src/
|   |   |-- components/          # Shared UI components
|   |   |-- pages/               # Login, home, admin, developer, operator, monitor pages
|   |   |-- types/               # Shared TypeScript types
|   |   |-- api.ts               # API client helpers
|   |   `-- App.tsx              # Application routing
|   |-- tests/                   # Frontend tests
|   |-- Dockerfile               # Frontend image
|   |-- package.json             # npm scripts and dependencies
|   `-- vite.config.ts           # Vite and API proxy configuration
|
|-- monitoring/
|   |-- prometheus.yml
|   `-- grafana/
|       |-- dashboards/
|       `-- provisioning/
|
|-- logs/                        # Mounted execution log directory
|-- docker-compose.yml           # Full local single-host stack
|-- compose-data.yml             # Data node compose file for distributed deployment
|-- compose-backend.yml          # Backend and worker compose file for distributed deployment
|-- compose-frontend.yml         # Frontend compose file for distributed deployment
|-- k6_load_test.js              # k6 load test
|-- k6_scenarios.json            # k6 scenario configuration
|-- phase2_test.js               # Additional phase 2 load test script
`-- README.md
```

## Quick Start

### Prerequisites

- Docker Desktop
- Git
- Node.js and npm, only required for local frontend development
- Python 3.11 recommended, only required for local backend development

### 1. Prepare Environment Files

Create the backend environment file from the example:

```powershell
copy backend\.env.example backend\.env
```

For Docker Compose, make sure `backend/.env` contains a database URL that points to the Compose database service:

```text
DATABASE_URL=mysql+pymysql://api_worker:PASSWORD_group11@db:3306/job_scheduler
```

### 2. Start the Full Stack

Run from the repository root:

```powershell
docker compose up -d --build
```

Open the application:

```text
http://localhost:3000
```

Check the backend health endpoint:

```powershell
curl.exe http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

### 3. Default Admin Account

On backend startup, the system ensures a built-in administrator account exists:

```text
Employee ID: admin
Password: admin
```

Use this account for initial administration and user management.

### 4. Useful Docker Commands

```powershell
# Show running services
docker compose ps

# Show all logs
docker compose logs

# Follow backend logs
docker compose logs -f backend

# Follow worker logs
docker compose logs -f worker

# Rebuild and restart all services
docker compose up -d --build

# Restart only the backend
docker compose restart backend

# Scale workers
docker compose up -d --scale worker=3

# Stop the stack
docker compose down
```

## Environment Variables

The backend uses `backend/.env` in Docker Compose and may use `.env.local` for local Python execution.

Required database variables:

| Variable | Description |
| --- | --- |
| `MYSQL_ROOT_PASSWORD` | MySQL root password used by the container |
| `MYSQL_DATABASE` | Database name created by the MySQL container |
| `MYSQL_USER` | Application database user |
| `MYSQL_PASSWORD` | Application database password |
| `DATABASE_URL` | SQLAlchemy database URL |

Runtime variables:

| Variable | Description | Default |
| --- | --- | --- |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Redis database index | `0` |
| `JOB_QUEUE_NAME` | Redis queue name | `job_priority_queue` |
| `HEARTBEAT_INTERVAL` | Worker heartbeat interval in seconds | `30` |
| `HEARTBEAT_TIMEOUT` | Worker heartbeat timeout in seconds | `60` |
| `DEFAULT_TASK_TIMEOUT` | Default job execution timeout in seconds | `300` |
| `MAX_EXECUTION_RETRIES` | Default retry limit | `1` |
| `LOG_ROOT` | Execution log root directory | `/app/logs` in Docker |

Password reset email variables:

| Variable | Description |
| --- | --- |
| `RESET_PASSWORD_BASE_URL` | Frontend URL used to generate reset links |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USE_TLS` | Whether SMTP uses TLS |
| `SMTP_FROM` | Sender email address |
| `SMTP_FROM_NAME` | Sender display name |
| `SMTP_USERNAME` | SMTP username |
| `SMTP_PASSWORD` | SMTP password or app password |

If SMTP is not configured, local development can still use the password reset flow by reading backend logs, depending on the current email helper behavior.

## Local Development

Docker Compose is the recommended way to run the complete system. The following commands are useful when developing one layer at a time.

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

When running the backend directly on the host machine, `DATABASE_URL` must point to a host-accessible database, for example:

```text
DATABASE_URL=mysql+pymysql://api_worker:PASSWORD_group11@localhost:3306/job_scheduler
```

The default `docker-compose.yml` keeps MySQL and Redis on the internal Docker network. If you want the host backend process to connect to Compose-managed MySQL and Redis, expose the required ports or use `compose-data.yml`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server normally opens at:

```text
http://localhost:5173
```

The frontend calls backend APIs through `/api`. In `frontend/vite.config.ts`, the current proxy target is:

```text
http://backend:8000
```

For direct local frontend development outside Docker, change the proxy target to:

```text
http://localhost:8000
```

## Testing

### Backend

```powershell
cd backend

# Run all backend tests
python -m pytest

# Run unit tests
python -m pytest -m unit

# Run integration tests
python -m pytest -m integration

# Run the syntax-level flake8 check used by CI
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

The backend CI workflow runs on Python 3.11 and executes flake8 plus pytest.

### Frontend

```powershell
cd frontend

# TypeScript type check
npm run typecheck

# Vitest
npm test

# Prettier check
npm run format:check

# Production build
npm run build
```

The frontend CI workflow runs on Node.js 22 and 24, then executes typecheck, Vitest, and Prettier check.

## Observability and Load Testing

### Metrics

The backend exposes Prometheus metrics at:

```text
http://localhost:8000/metrics
```

Prometheus is available at:

```text
http://localhost:9090
```

Grafana is available at:

```text
http://localhost:3001
```

Default Grafana credentials:

```text
Username: admin
Password: admin
```

Provisioned dashboards and data sources are stored under `monitoring/grafana`.

### k6 Load Tests

The repository includes k6 scripts for load and phase testing:

```powershell
k6 run k6_load_test.js
k6 run phase2_test.js
```

InfluxDB is included in the Compose stack for k6 time-series output.

## Distributed Deployment

In addition to the single-host `docker-compose.yml`, the repository provides split Compose files for distributed deployment:

| File | Intended role |
| --- | --- |
| `compose-data.yml` | Runs MySQL, Redis, scheduler, Prometheus, InfluxDB, and Grafana |
| `compose-backend.yml` | Runs backend API and worker services that connect to the data node |
| `compose-frontend.yml` | Runs the frontend service |

Before using the distributed Compose files, update service IP addresses and environment variables to match the target machines. In particular:

- `DATABASE_URL` should point to the machine running MySQL.
- `REDIS_HOST` should point to the machine running Redis.
- `VITE_API_URL` should point to the public API endpoint or load balancer used by the browser.

Example startup commands:

```powershell
# On the data node
docker compose -f compose-data.yml up -d --build

# On the backend node
docker compose -f compose-backend.yml up -d --build

# On the frontend node
docker compose -f compose-frontend.yml up -d --build
```

## Troubleshooting

### Frontend Shows `Failed to fetch`

Check the backend health endpoint:

```powershell
curl.exe http://localhost:8000/api/health
```

If the backend is healthy, verify the frontend API target:

- Docker frontend: use `http://localhost:3000`
- Local Vite frontend: confirm `frontend/vite.config.ts` proxies `/api` to the correct backend URL
- Distributed frontend: confirm `VITE_API_URL` points to the reachable API or load balancer

### Backend Cannot Connect to MySQL

Check the following:

- `backend/.env` exists.
- `DATABASE_URL` is set.
- Docker Compose mode uses `db` as the MySQL host.
- Local Python mode uses `localhost` or another host-accessible MySQL address.
- Existing Docker volumes may contain old schemas; restart or recreate volumes only when you intentionally want a clean database.

### Redis Queue Is Not Consumed

Check the following:

- `redis` service is running.
- `worker` service is running.
- Backend and worker use the same `REDIS_HOST`, `REDIS_PORT`, and `JOB_QUEUE_NAME`.
- Worker logs do not show task validation or execution errors.

### Password Reset Email Fails

For Gmail SMTP:

1. Enable 2-Step Verification on the sender account.
2. Create a Gmail App Password.
3. Use the full sender email as `SMTP_USERNAME`.
4. Use the 16-character app password as `SMTP_PASSWORD`.
5. Restart the backend after changing environment variables:

```powershell
docker compose restart backend
```

### Code Changes Do Not Take Effect

Restart the affected service:

```powershell
docker compose restart backend
docker compose restart worker
docker compose restart scheduler
```

If dependencies, Dockerfiles, or build configuration changed, rebuild:

```powershell
docker compose up -d --build
```
