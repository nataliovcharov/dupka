# Deployment

How Dupka runs in production, and how to set it up from scratch. Why this setup: `docs/decisions/0002-hosting.md`.

- **Backend:** one Oracle Cloud Always Free VM (ARM, 2 OCPU, 12 GB) running `compose.prod.yaml`: Postgres with PostGIS, a one-off `migrate` job, the API, the worker and Caddy for HTTPS.
- **Frontend:** Cloudflare Pages, built from `frontend/`.

## 1. Oracle account

1. Sign up at https://www.oracle.com/cloud/free/. Pick a home region close to Skopje (Frankfurt or Amsterdam). It can't be changed later.
2. A card is needed to verify the signup. Keep the account **Always Free**, don't upgrade to Pay-As-You-Go, so nothing can be billed.

## 2. The VM

1. SSH key on your Mac:

   ```
   ssh-keygen -t ed25519 -f ~/.ssh/dupka_oracle
   ```

2. Compute > Instances > Create instance:
   - Image: **Canonical Ubuntu 24.04** (the aarch64 one)
   - Shape: **VM.Standard.A1.Flex**, 2 OCPU, 12 GB memory
   - Boot volume: 100 GB
   - SSH key: paste `~/.ssh/dupka_oracle.pub`

   If it says "out of capacity", try again later or another availability domain.

3. Open ports 80 and 443: Networking > Virtual cloud networks > your VCN > Security lists > Default > Add ingress rules, source `0.0.0.0/0`, TCP, destination ports `80` and `443`.

4. Connect (the public IP is on the instance page):

   ```
   ssh -i ~/.ssh/dupka_oracle ubuntu@PUBLIC_IP
   ```

5. Oracle's Ubuntu image also blocks ports in its own firewall. On the VM:

   ```
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

6. Automatic security updates:

   ```
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y unattended-upgrades
   ```

## 3. Docker

Official apt repository (https://docs.docker.com/engine/install/ubuntu/):

```
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and back in, so `docker` works without `sudo`.

## 4. Dupka

1. Code:

   ```
   sudo mkdir -p /opt/dupka && sudo chown ubuntu /opt/dupka
   git clone https://github.com/nataliovcharov/dupka.git /opt/dupka
   ```

2. Models (not in Git). From your Mac:

   ```
   scp -i ~/.ssh/dupka_oracle ~/code/personal/dupka/ml/models/e001-best.pt ~/code/personal/dupka/ml/models/face_detection_yunet_2023mar.onnx ~/code/personal/dupka/ml/models/yolo-v9-s-608-license-plates-end2end.onnx ubuntu@PUBLIC_IP:/opt/dupka/ml/models/
   ```

3. Settings, on the VM:

   ```
   cd /opt/dupka
   cp .env.prod.example .env.prod
   nano .env.prod
   ```

   Fill in the passwords (generate them, see the comments), `API_DOMAIN` (for the IP `1.2.3.4` use `1-2-3-4.sslip.io`) and `CORS_ORIGINS` (the Cloudflare Pages address).

4. Start:

   ```
   docker compose -f compose.prod.yaml --env-file .env.prod up -d --build
   ```

   The first build takes a while (PyTorch). Check it:

   ```
   docker compose -f compose.prod.yaml --env-file .env.prod ps
   curl https://API_DOMAIN/health
   ```

## 5. Frontend on Cloudflare Pages

1. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git, pick `nataliovcharov/dupka`.
2. Build settings:
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
   - Environment variable: `VITE_API_URL` = `https://API_DOMAIN`
3. Pages builds on every push to `main`. Paths like `/admin` and `/privacy` are served by `index.html`.
4. Put the Pages address in `CORS_ORIGINS` on the VM and restart the API.

## Updating

On the VM:

```
cd /opt/dupka
git pull
docker compose -f compose.prod.yaml --env-file .env.prod up -d --build
```

The `migrate` service runs new migrations before the API starts.

## Logs

```
docker compose -f compose.prod.yaml --env-file .env.prod logs -f api worker
```
