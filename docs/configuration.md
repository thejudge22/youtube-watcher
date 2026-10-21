# Configuration

YouTube-Watcher is configured with environment variables, normally set in the `.env` file next to `docker-compose.yml`. Start from [`.env.example`](../.env.example). Restart the container after changing `.env`:

```bash
docker compose up -d
```

App behaviour such as auto-refresh, backups, Shorts detection and the HTTP timeout is set in the app itself, under **Settings**. See the [User Guide](user-guide.md#settings).

## Environment variables

| Variable | Default | What it does |
|----------|---------|--------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/youtube-watcher.db` | Where the SQLite database lives. Backups are written to a `backups` folder next to it. |
| `BACKEND_HOST` | `0.0.0.0` | Address the server listens on inside the container. |
| `BACKEND_PORT` | `8000` | Port the server listens on inside the container. Change the left side of `ports:` in `docker-compose.yml` to use a different port on your machine. |
| `AUTH_ENABLED` | `false` | Require a login. See [Authentication](#authentication). |
| `AUTH_USERNAME` | (empty) | Login username, when `AUTH_ENABLED=true`. |
| `AUTH_PASSWORD_HASH` | (empty) | Hashed login password, when `AUTH_ENABLED=true`. |
| `JWT_SECRET_KEY` | (generated) | Secret used to sign login sessions. If unset, one is generated once and kept in `data/.jwt_secret`. |
| `JWT_EXPIRE_HOURS` | `336` (14 days) | How long you can go without opening the app before you have to log in again. |
| `API_KEY` | (empty) | Key for scripts and other programs. See [API key access](#api-key-access). |
| `ALLOWED_HOSTS` | (empty) | Comma-separated host names or IPs used to reach the app. Requests for any other host are rejected. |
| `CORS_ORIGINS` | (empty) | Comma-separated origins allowed to call the API from a browser on another site. |

## Authentication

Login is off by default. Turn it on whenever the app is reachable from a network you don't fully trust. With it off, any web page you visit could reach the app's API through DNS rebinding.

### Username and password

1. Generate a password hash:

   ```bash
   ./scripts/generate-password-hash.sh
   ```

2. Set these in `.env`:

   ```ini
   AUTH_ENABLED=true
   AUTH_USERNAME=admin
   AUTH_PASSWORD_HASH=<hash from the script>
   ```

3. Restart the container.

Sessions renew automatically while you use the app, so you only log in again after going `JWT_EXPIRE_HOURS` (14 days by default) without opening it. Restarting the server doesn't log you out.

After 10 failed logins from one IP address within 15 minutes, further attempts from that address are refused until the 15 minutes are up. Behind a reverse proxy every client may appear to come from the proxy's address, so one lockout then applies to everyone until it expires.

When login is on, the interactive API docs at `/docs` are hidden.

### API key access

Scripts and other programs can call the API with a key instead of logging in.

1. Generate a key:

   ```bash
   ./scripts/generate-api-key.sh
   ```

2. Set it in `.env`:

   ```ini
   API_KEY=<key from the script>
   ```

3. Send it with each request:

   ```bash
   curl http://localhost:38000/api/channels \
     -H "X-API-Key: <your-api-key>"
   ```

## Restricting host names

Set `ALLOWED_HOSTS` to the names or addresses you use to reach the app, for example:

```ini
ALLOWED_HOSTS=watcher.example.com,192.168.1.10
```

Requests addressed to any other host are rejected, which blocks DNS-rebinding attacks. `localhost` and `127.0.0.1` are always allowed.

## API documentation

With login off, interactive API docs are served at `/docs` (for example http://localhost:38000/docs).

## Docker image tags

- `:latest` is rebuilt from every commit to the main branch.
- Each release also publishes a pinned tag named after its date, such as `:v2026-10-21`. Use one if you want to choose when to upgrade.
