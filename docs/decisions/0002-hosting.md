# 0002. Free hosting

**Status:** Accepted, 2026-09-30

## Context
Dupka has to stay free to run. The pieces are a FastAPI API, a worker, Postgres with PostGIS, photo storage and a static React frontend. The worker is the hard part: PyTorch, CLIP, YOLO and the blur models need about 3 GB of RAM, it runs all the time, and it has to reach Postgres.

Free options checked (September 2026):

| Option | What's free | Why it does or doesn't fit |
|---|---|---|
| Oracle Cloud Always Free, Ampere A1 | 2 OCPU, 12 GB RAM, 200 GB disk, 20 GB object storage | The only free option with enough RAM for the worker |
| Hugging Face Spaces (free CPU) | 2 vCPU, 16 GB RAM | Sleeps when unused, disk isn't persistent, only ports 80/443/8080 go out, so it can't reach Postgres |
| Neon (free) | 0.5 GB Postgres | Scales to zero, 100 compute hours a month. A worker polling every 2 s uses them up in about 17 days |
| Supabase (free) | 500 MB Postgres with PostGIS | Works for the database alone, doesn't solve the worker |
| Cloudflare R2 | 10 GB storage | Needs a payment method to turn on |
| Cloudflare Pages | Static hosting | Fits the frontend, no card needed |

## Decision
- **Backend on one Oracle Always Free VM** (VM.Standard.A1.Flex, 2 OCPU, 12 GB, Ubuntu, ARM), running Docker Compose: API, worker, Postgres with PostGIS and Caddy (HTTPS). Same setup as local development.
- **Photos on the VM's disk.** A VM's disk persists, so `LocalStorage` keeps working. Nightly backups of the database and photos go to Oracle Object Storage.
- **Frontend on Cloudflare Pages.** It sends every path to `index.html`, so `/admin` and `/privacy` work.
- **Address:** the API starts on a free `sslip.io` name for the VM's IP, with a Let's Encrypt certificate from Caddy. A real domain can replace it by changing `API_DOMAIN`.
- **The account stays Always Free**, not Pay-As-You-Go, so nothing can be billed. Oracle needs a card only to verify the signup.

## Consequences
- **Vendor risk:** Oracle halved the free A1 limits in June 2026 without announcing it. Because everything runs in Docker Compose, moving to a small paid VM elsewhere takes hours, not a rewrite.
- **Idle reclamation:** Oracle reclaims Always Free instances when CPU, network and memory all stay under 20% for 7 days. The loaded models use about 25% of memory.
- **ARM:** the official `postgis/postgis` image is amd64 only. Production builds its own image from `postgres:17` with Debian's PostGIS package (`deploy/db`). PyTorch comes from the CPU-only index on Linux, so the image doesn't pull in CUDA.
- **We run the server:** OS updates, firewall and backups are on us. See `docs/deployment.md`.
