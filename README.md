# Personal AI

A small self-hosted AI workspace I run on a single VPS. It keeps Open WebUI and CLI agents behind Tailscale-only access, with a simple bootstrap script and minimal Docker operations.

For someone browsing my projects, this is intentionally pragmatic infrastructure work: lightweight automation, secure-by-default remote access, and a setup I can rebuild quickly without adding more platform than I need.

## Command Reference

Bootstrap a fresh Debian or Ubuntu VPS as `root` by downloading the script first:

```bash
curl -fsSL https://raw.githubusercontent.com/jgoodhcg/personal-ai/main/scripts/setup.sh -o /root/setup.sh
chmod +x /root/setup.sh
PROJECT_USER=<your-user> TS_AUTHKEY=<your-tailscale-auth-key> /root/setup.sh
```

Or use the interactive Tailscale login flow:

```bash
curl -fsSL https://raw.githubusercontent.com/jgoodhcg/personal-ai/main/scripts/setup.sh -o /root/setup.sh
chmod +x /root/setup.sh
PROJECT_USER=<your-user> /root/setup.sh
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
docker compose logs -f searxng
docker compose pull
tailscale status
```

## First Run

- Recommended: create a one-off or reusable auth key in the Tailscale admin console and pass it as `TS_AUTHKEY` during setup.
- If you omit `TS_AUTHKEY`, the script prompts on the terminal and `tailscale up` prints a login URL; open it in a browser and sign in to attach the server to your tailnet.
- You do not pre-create the device in Tailscale. The device appears when you authenticate it.
- If your tailnet uses device approval, approve the new machine in the Tailscale admin console before expecting traffic to work.
- The script creates one non-root Linux user for the project, adds it to `sudo` and `docker`, and clones the repo into that user's home directory.
- Package upgrades keep your existing `sshd_config` by default, suppress `needrestart` prompts, and are meant to run cleanly on a fresh VPS without blocking TUI dialogs.

## Deploying Updates

From your laptop (requires Tailscale):

```bash
ssh personal-ai@personal-ai
cd /home/personal-ai/personal-ai
git pull --ff-only
docker compose config
docker compose up --dry-run
docker compose pull
docker compose up -d
docker compose ps
exit  # disconnect
```

> This example assumes the default project user is `personal-ai` and the repo lives at `/home/personal-ai/personal-ai`.

- Use `docker compose up -d`, not plain `docker compose up`, for routine updates. Detached mode returns your shell immediately; attached mode tails logs and `Ctrl+C` stops the stack.
- `docker compose down` is not required for normal image updates. `docker compose pull` followed by `docker compose up -d` recreates changed services with less downtime.
- If SearXNG logs that an update is available for `/etc/searxng/settings.yml`, review and merge the bind-mounted files at `searxng/settings.yml` and `searxng/settings.yml.new`, then run `docker compose up -d` again.
- If you chose a different `PROJECT_USER` during setup, replace both instances of `personal-ai` in the SSH command and path with that username.

## Notes

- `data/` holds persistent Open WebUI state and stays out of git.
- `.env` is local-only and should contain secrets copied from `.env.example`.
- The intended access path is Tailscale, not public internet exposure.
- Running a downloaded script file is preferred over `curl | bash` because package-manager and Tailscale login prompts behave more reliably with a normal TTY.
- If you prefer cloning instead of `curl`, clone into `/root`, run `scripts/setup.sh`, and let the script place the real working copy under `/home/<project-user>/personal-ai`.
