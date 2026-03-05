# Personal AI

A small self-hosted AI workspace I run on a single VPS. It keeps Open WebUI and CLI agents behind Tailscale-only access, with a simple bootstrap script and minimal Docker operations.

For someone browsing my projects, this is intentionally pragmatic infrastructure work: lightweight automation, secure-by-default remote access, and a setup I can rebuild quickly without adding more platform than I need.

## Command Reference

Bootstrap a fresh Debian or Ubuntu VPS as `root`:

```bash
git clone https://github.com/justingood/personal-ai.git
cd personal-ai
ADMIN_USER=<your-admin-user> TS_AUTHKEY=<your-tailscale-auth-key> bash scripts/setup.sh
```

Or use the interactive Tailscale login flow:

```bash
git clone https://github.com/justingood/personal-ai.git
cd personal-ai
ADMIN_USER=<your-admin-user> bash scripts/setup.sh
```

Validate the Docker Compose config:

```bash
docker compose config
docker compose up --dry-run
docker compose ps
```

Common operations:

```bash
docker compose up -d
docker compose down
docker compose logs -f chat
docker compose pull
tailscale status
```

## First Run

- Recommended: create a one-off or reusable auth key in the Tailscale admin console and pass it as `TS_AUTHKEY` during setup.
- If you omit `TS_AUTHKEY`, the script pauses and `tailscale up` prints a login URL; open it in a browser and sign in to attach the server to your tailnet.
- You do not pre-create the device in Tailscale. The device appears when you authenticate it.
- If your tailnet uses device approval, approve the new machine in the Tailscale admin console before expecting traffic to work.

## Notes

- `data/` holds persistent Open WebUI state and stays out of git.
- `.env` is local-only and should contain secrets copied from `.env.example`.
- The intended access path is Tailscale, not public internet exposure.
- On a brand-new VPS, `scripts/setup.sh` creates both the admin user and the agent user for you.
