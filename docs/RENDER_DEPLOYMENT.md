# DentiFlow Render Deployment

## Status

The repository is prepared for a Render Python web service. A public Render URL cannot be created from this workspace because GitHub repository access and Render account credentials are not available here. Do not invent a URL until Render reports a successful deploy.

## Web service settings

- Service type: Web Service
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`
- Health check path: `/api/health`
- Branch: the selected production branch
- Auto-deploy: enabled

`render.yaml` contains the reproducible web-service configuration and secret placeholders. Do not put passwords in that file.

## Required Render environment variables

Set these in Render's Environment tab. Never commit their values:

- `APP_ENV=production`
- `FLASK_DEBUG=0`
- `SESSION_COOKIE_SECURE=1`
- `MYSQL_HOST=<private MySQL hostname>`
- `MYSQL_PORT=3306`
- `MYSQL_DATABASE=dentiflow`
- `MYSQL_USER=<dedicated non-root MySQL user>`
- `MYSQL_PASSWORD=<secret MySQL password>`
- `SECRET_KEY=<long random application secret>`

Production configuration rejects `localhost` and `127.0.0.1` as `MYSQL_HOST`.

## MySQL

Use a persistent MySQL 8-compatible service that is reachable over a private network. Configure the application with its internal hostname, not a public URL and not `localhost`. Create the `dentiflow` database and a dedicated non-root user. If the Render account does not provide a private MySQL service, use an external managed MySQL 8 provider with private/network-restricted access rather than changing the application to SQLite.

Run the non-destructive initialization once after setting the production environment:

```text
python init_db.py
```

This creates missing tables and preserves existing records. `setup_database.py` is intended for local setup and may seed demo data. Do not run a demo reset against production. The destructive seed reset requires both `DENTIFLOW_DEMO_RESET=1` and `DENTIFLOW_ALLOW_DEMO_RESET=1` and should remain a local/demo-only operation.

## GitHub steps

1. Ensure `.env`, `.venv/`, `__pycache__/`, `*.pyc`, and `*.db` are ignored.
2. Create or select a private GitHub repository.
3. Push this project to the selected branch.
4. Confirm `.env` and `database.db` are not in the commit history or working tree.
5. In Render, choose **New + > Web Service** and connect the repository.
6. Choose the production branch and enable automatic deploys.
7. Enter the build, start, and health settings above.
8. Add the environment variables in Render's dashboard.
9. Deploy and wait for a healthy status.

## Post-deploy checks

Open the generated HTTPS URL and test:

- `/`
- `/login`
- `/dashboard` after login
- `/patients`
- `/appointments`
- `/queue`
- `/clinical`
- `/treatment-plans`
- `/billing`
- `/inventory`
- `/staff`
- `/reports`
- `/branches`
- `/operations`
- `/settings`
- `/book`
- `/portal`
- `/api/health`

Expected health response:

```json
{
  "status": "ok",
  "database": "mysql",
  "database_connected": true
}
```

## Demo credentials

Demo credentials are for local/demo use only and must not be treated as production secrets. The seeded demo doctor is documented separately from deployment secrets.
