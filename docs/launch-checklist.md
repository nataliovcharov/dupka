# Launch checklist

Things that must be done before Dupka is public. Tick them off in the PR that does them.

## Privacy

- [ ] Contact email on the privacy page (`frontend/src/components/PrivacyPage.tsx`), for questions and removal requests
- [x] Faces and plates blurred before a photo can be public (`docs/moderation.md`)
- [x] Photos of hidden reports deleted after 30 days (`HIDDEN_PHOTO_DAYS`)
- [x] Privacy page linked from the report form

## Security

- [ ] Strong `ADMIN_TOKEN` set on the server, not the one from development
- [x] Upload rate limit per IP (`UPLOAD_RATE_LIMIT`)
- [ ] uvicorn trusts the host's proxy (`--forwarded-allow-ips`), otherwise the rate limit sees one IP for everyone
- [ ] More than one API process: move the rate limit counters to a shared store (Redis)
- [ ] CORS allows only the frontend's domain, if the frontend and API are on different domains

## Hosting

- [ ] Photos in object storage, not on the server's disk (a new `Storage` class)
- [ ] Postgres with PostGIS, migrations run on deploy (`alembic upgrade head`)
- [ ] Worker with enough memory for PyTorch, CLIP, YOLO and the blur models (about 2 GB)
- [ ] Model files downloaded on the worker (they're not in Git)
- [ ] Frontend host sends every path (`/admin`, `/privacy`) to `index.html`
- [ ] `VITE_API_URL` set for the frontend build
