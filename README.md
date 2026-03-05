# Personal AI

A small self-hosted AI workspace I run on a single VPS. It keeps Open WebUI and CLI agents behind Tailscale-only access, with a simple bootstrap script and minimal Docker operations.

For someone browsing my projects, this is intentionally pragmatic infrastructure work: lightweight automation, secure-by-default remote access, and a setup I can rebuild quickly without adding more platform than I need.

## Command Reference

Bootstrap a fresh Debian or Ubuntu VPS as `root` without cloning the repo first:

```bash
curl -fsSL https://raw.githubusercontent.com/justingood/personal-ai/main/scripts/setup.sh | PROJECT_USER=<your-user> TS_AUTHKEY=<your-tailscale-auth-key> bash
```

Or use the interactive Tailscale login flow:

```bash
curl -fsSL https://raw.githubusercontent.com/justingood/personal-ai/main/scripts/setup.sh | PROJECT_USER=<your-user> bash
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
- The script creates one non-root Linux user for the project, adds it to `sudo` and `docker`, and clones the repo into that user's home directory.

## Notes

- `data/` holds persistent Open WebUI state and stays out of git.
- `.env` is local-only and should contain secrets copied from `.env.example`.
- The intended access path is Tailscale, not public internet exposure.
- If you prefer cloning instead of `curl`, clone into `/root`, run `scripts/setup.sh`, and let the script place the real working copy under `/home/<project-user>/personal-ai`.
