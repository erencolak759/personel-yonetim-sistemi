# Personnel Management System

This repository contains a modern full-stack personnel management system. It uses a pnpm monorepo with a TypeScript React frontend and a Python Flask backend (SQLite database).

## Technologies

Frontend:
- React 18 with TypeScript
- Vite as development server and bundler
- Tailwind CSS for styling
- React Router (v6) for routing
- TanStack React Query for server state
- Axios for HTTP requests

Backend:
- Python 3.10+ with Flask
- SQLite database (file: `apps/backend/database.db`)
- Werkzeug for password hashing

## Project structure

```
personel-yonetim-sistemi/
├── apps/
│   ├── backend/          # Flask API (apps/backend)
│   │   ├── api/          # Blueprint endpoints (auth, employee, leave, settings, ...)
│   │   ├── utils/        # DB helpers and utilities
│   │   ├── app.py        # Flask app entry
│   │   └── requirements.txt
│   └── frontend/         # React + TypeScript UI (apps/frontend)
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── contexts/
│       │   └── lib/
│       └── package.json
├── package.json          # Root pnpm workspace config
├── pnpm-workspace.yaml
└── .nvmrc
```

## Features (high level)

- Role-based UI (admin and user areas). Frontend routes are split under `/admin/*` and `/user/*`.
- User accounts are tied to personnel records. Creating a personnel record requires creating a corresponding login account.
- First-login password change enforcement: admin-created accounts are required to change password on first login.
- Users can edit their own profile under `user/settings` (endpoint: `PUT /api/employees/me`).
- Backend enforces authorization on protected endpoints (decorators) and returns a silent `authenticated: false` response for `GET /api/auth/me` when no token is present (avoids noisy errors).

## Getting started

### Prerequisites

- Node.js 18+
- pnpm 8+
- Python 3.10+

### Quick Install (one-liners)

The following commands clone the repository, run the appropriate setup script for your platform, and prepare the application for development.

```bash
# macOS/Linux: clone and setup in one line (copy-paste and run)
bash -c "git clone https://github.com/erencolak759/personel-yonetim-sistemi.git && cd personel-yonetim-sistemi && bash scripts/setup.sh"

# Windows (PowerShell): clone and setup in one line
powershell -Command "git clone https://github.com/erencolak759/personel-yonetim-sistemi.git; Set-Location personel-yonetim-sistemi; .\\scripts\\setup.ps1"
```

### Manual Install
- macOS / Linux (zsh / bash):

```bash
# Clone repository
git clone https://github.com/erencolak759/personel-yonetim-sistemi.git
cd personel-yonetim-sistemi

# Run the setup script (creates venv, installs Python dependencies, runs pnpm install, copies .env.example -> .env if missing,
# and initializes the database unless SKIP_DB_INIT=1 is set)
bash scripts/setup.sh
```

- Windows (PowerShell):

```powershell
# Clone repository
git clone https://github.com/erencolak759/personel-yonetim-sistemi.git
cd personel-yonetim-sistemi

# Run the setup script (may require admin rights for ExecutionPolicy the first time)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Notes:
- If a remote database (e.g., Railway) is already set up and you want to skip the database initialization/seed steps, use the `SKIP_DB_INIT=1` environment variable. Example:

```bash
SKIP_DB_INIT=1 bash scripts/setup.sh
```

- If you want to skip automatic pip installation (e.g., in CI environments), use `SKIP_PIP_INSTALL=1`.

### Fast Start

You can run the app with:
```bash
pnpm install:all
pnpm dev
```

### Manuel Start

From repository root:

```bash
pnpm install
```

Backend setup:

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate    # on macOS / Linux
pip install -r requirements.txt
```

To run backend alone:

```bash
cd apps/backend
source venv/bin/activate
python app.py
```
To run frontend alone:

```bash
cd apps/frontend
pnpm dev
```

Default hosts/ports used in development (can be configured in project files):

- Frontend (Vite): http://localhost:5173
- Backend (Flask): http://localhost:8080  (API prefix: `/api`)

## API (summary)

This is a short list of the most-used API endpoints. See the source under `apps/backend/api` for full details.

### Auth
- `POST /api/auth/login` — login, returns JWT and user info
- `POST /api/auth/logout` — logout (stateless)
- `GET /api/auth/me` — returns `{ authenticated: true|false, user?: {...} }`; when no token present it returns `authenticated: false` (200)
- `POST /api/auth/change-password` — change password; returns a new token and user object on success

### Users / Personnel
- `GET /api/employees` — list active personnel
- `GET /api/employees/:id` — personnel details
- `POST /api/employees` — create personnel **(requires `kullanici_adi` and `sifre` in request body; a linked user account is created)**
- `PUT /api/employees/:id` — update personnel (admin)
- `DELETE /api/employees/:id` — soft-delete personnel (also deactivates linked user account)
- `PUT /api/employees/me` — update currently authenticated user’s personnel data

### User administration
- `GET /api/users` — list user accounts (admin)
- `POST /api/users` — create user (admin)
- `PUT /api/users/:id` — update user (admin)
- `DELETE /api/users/:id` — deactivate user (admin)

### Leaves / Time off
- `GET /api/leaves` — list leaves
- `POST /api/leaves` — create leave request (backend enforces that non-admins can only create leaves for themselves)

### Settings
- `GET/POST /api/settings/departments`
- `GET/POST /api/settings/positions`
- `GET/POST /api/settings/leave-types`

## Default admin account

When seeding the database, a default admin account is created:

- Username: `admin`
- Password: `admin123`

Change this account or the credentials in production.

## Notes and development guidance

- The backend stores password hashes in the `Kullanici` table and links users to `Personel` via `personel_id`.
- Creating personnel via the frontend now requires the account fields (`kullanici_adi` and `sifre`) and assigns a `rol`.
- The frontend contains role-aware routes and components (see `apps/frontend/src/App.tsx` and `src/components/Layout.tsx`).
