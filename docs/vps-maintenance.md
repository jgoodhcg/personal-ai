# Production VPS Maintenance

This runbook covers routine maintenance for the Ubuntu 24.04 LTS VPS that hosts
Open WebUI and SearXNG. Run commands over the Tailscale SSH connection from the
repository directory.

Persistent application state lives in `data/`. Never remove that directory or
prune Docker volumes as part of routine maintenance.

## Suggested cadence

- Weekly: check service state, disk usage, and available package updates.
- Monthly: install Ubuntu updates and remove dangling Docker images.
- Before an application update: confirm adequate free disk space.
- After maintenance: validate and inspect both services.

Use the VPS provider's snapshot or backup facility before higher-risk system
maintenance. Confirm that a recent backup exists before making filesystem,
Docker storage, or operating-system changes.

## Routine health check

```bash
tailscale status
docker compose ps
df -h /
df -ih /
docker system df
```

Investigate when the root filesystem reaches about 80% usage. Docker image pulls
need room for both the downloaded layers and their extracted contents, so keep at
least 5–10 GB free before pulling the Open WebUI image.

To inspect Docker disk usage in detail:

```bash
docker system df -v
docker image ls --filter dangling=true
```

## Update Ubuntu

Review and install package updates:

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
sudo apt autoremove
sudo apt clean
```

`apt autoremove` shows what it will remove and asks for confirmation. Review the
list before accepting it.

Check whether Ubuntu requires a reboot:

```bash
if [ -f /var/run/reboot-required ]; then cat /var/run/reboot-required; fi
```

If a reboot is required, first verify that Docker services use the configured
`restart: unless-stopped` policy:

```bash
docker compose config --quiet
docker compose ps
```

Reboot during an acceptable maintenance window:

```bash
sudo reboot
```

Reconnect over Tailscale after the VPS returns, then run the
[post-maintenance checks](#post-maintenance-checks).

## Update application images

Check disk space before pulling:

```bash
df -h /
docker system df -v
```

Remove old dangling image versions:

```bash
docker image prune
```

This removes only untagged images that no container uses. It does not remove
containers, tagged images, volumes, or `data/`. Review Docker's summary before
confirming. Do not substitute `docker system prune` or `docker volume prune`.

Pull and deploy:

```bash
docker compose pull
docker compose up --dry-run
docker compose up -d
docker compose ps
```

`docker compose pull` downloads images but does not update running containers.
`docker compose up -d` recreates services when their images changed; running it
does not require a preceding `docker compose down`.

After confirming that the updated services work, run `docker image prune` again
to remove the image versions replaced during deployment.

## Recover from `no space left on device`

If an image pull fails while registering or extracting a layer:

1. Do not delete `data/`, Docker volumes, or files under `/var/lib/docker`.
2. Check whether disk blocks or inodes are exhausted:

   ```bash
   df -h /
   df -ih /
   docker system df -v
   docker compose ps
   ```

3. Remove dangling images:

   ```bash
   docker image prune
   df -h /
   ```

4. Once at least 5–10 GB is available, retry the pull and deployment:

   ```bash
   docker compose pull
   docker compose up --dry-run
   docker compose up -d
   docker compose ps
   ```

Docker reuses layers that completed downloading before the failure.

On 2026-07-29, a failed Open WebUI pull left the 48 GB root filesystem at 96%
usage. Old untagged Open WebUI and SearXNG images had accumulated over several
updates; `docker image prune -f` reclaimed 32.53 GB. This is why image cleanup is
part of the monthly and post-deployment procedures.

If dangling images do not provide enough space, inspect the largest consumers
before deleting anything:

```bash
sudo du -xhd1 /var/lib/docker /var/log 2>/dev/null | sort -h
journalctl --disk-usage
```

Large system journals can be reduced without touching application data:

```bash
sudo journalctl --vacuum-size=200M
```

If several gigabytes still cannot be freed safely, expand the VPS disk rather
than applying broader Docker cleanup.

## Post-maintenance checks

```bash
tailscale status
docker compose ps
docker compose logs --tail=100 chat
docker compose logs --tail=100 searxng
df -h /
```

Confirm that both services are running, Open WebUI loads through its Tailscale
URL, and a web search succeeds.

## Prohibited routine cleanup

Do not use these commands for routine maintenance:

- `docker system prune` — broad cleanup can remove resources needed for recovery.
- `docker volume prune` or `docker compose down -v` — can remove persistent data.
- Manual deletion inside `/var/lib/docker` — can corrupt Docker's storage state.
- Any removal under `data/` — this is the persistent Open WebUI state.
