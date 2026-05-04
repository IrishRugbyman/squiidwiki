# SquiidWiki — Deployment Guide

Self-hosted on a single Hetzner VPS. Serves a small group of trusted users.

---

## 0. Before you start — what you need

### 0a. A domain name

You need a domain so your friends can reach the app at something like `wiki.lbzgiu.xyz` instead of a raw IP.

> You already bought `lbzgiu.xyz` on Namecheap and pointed it at Cloudflare. You'll use `wiki.lbzgiu.xyz` for this project. Other future projects get their own subdomain (e.g. `app.lbzgiu.xyz`) for free.

### 0b. Your SSH key (generated on your Windows machine)

SSH is how you securely connect to the server from your PC. You need a key pair — a private key that stays on your machine and a public key you give to Hetzner.

Open **PowerShell** or **Windows Terminal** and run:

```powershell
ssh-keygen -t ed25519 -C "lbzgiu-server"
```

- When asked for a file path, press **Enter** to use the default (`C:\Users\irish\.ssh\id_ed25519`)
- When asked for a passphrase, either set one (more secure) or press **Enter** twice to skip

This creates two files:
- `C:\Users\irish\.ssh\id_ed25519` — your **private key**, never share this
- `C:\Users\irish\.ssh\id_ed25519.pub` — your **public key**, you'll give this to Hetzner

Print your public key so you can copy it:

```powershell
cat C:\Users\irish\.ssh\id_ed25519.pub
```

It will look like: `ssh-ed25519 AAAAC3Nza... lbzgiu-server`. Copy the whole line.

---

## 1. Create the Hetzner server

### 1a. Create a Hetzner account

Go to [console.hetzner.cloud](https://console.hetzner.cloud/), sign up, and verify your email. You'll need to add a payment method (credit card or PayPal).

### 1b. Create a new project

1. Click **+ New project**
2. Name it `lbzgiu` (general — this server will host multiple projects)
3. Click **Add project**

### 1c. Add your SSH key to Hetzner

Before creating the server, register your public key so Hetzner can install it automatically:

1. In your project, go to **Security** (left sidebar) → **SSH Keys**
2. Click **Add SSH key**
3. Paste the public key you copied in step 0b
4. Name it `my-laptop` or similar
5. Click **Add SSH key**

### 1d. Create the server

1. Click **+ Create server** (top right)
2. **Location**: Falkenstein (`fsn1`) or Nuremberg (`nbg1`) — EU, low latency
3. **Image**: Ubuntu **24.04** (under "Linux")
4. **Type**: Shared vCPU → x86 → **CX22** (2 vCPU, 4 GB RAM, ~€4.50/mo)
5. **Networking**: leave defaults (public IPv4 + IPv6 enabled)
6. **SSH keys**: tick the key you just added
7. **Name**: `lbzgiu-vps`
8. Click **Create & buy now**

The server will be ready in about 30 seconds. You'll see its **public IPv4 address** on the server page — copy it, you'll need it.

### 1e. Connect to the server from your PC

Open PowerShell and SSH in as root:

```powershell
ssh root@YOUR_SERVER_IP
```

If asked "Are you sure you want to continue connecting?" type `yes` and press Enter.

You are now inside the server. All commands from here run on the remote machine, not your PC.

---

## 2. Initial server setup

You are logged in as `root`. First, create a regular user so you're not running everything as root (bad security practice):

```bash
# Create user named "lbzgiu" — this is the general server user for all projects
adduser lbzgiu
# You'll be asked for a password — set one, then press Enter through the rest of the prompts
```

```bash
# Give that user sudo (admin) privileges
usermod -aG sudo lbzgiu
```

```bash
# Copy root's SSH key to the new user so you can log in as lbzgiu too
rsync --archive --chown=lbzgiu:lbzgiu ~/.ssh /home/lbzgiu
```

Now harden SSH — prevent anyone from logging in as root or using passwords (keys only):

```bash
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh
```

Set up the firewall — only allow SSH, HTTP, and HTTPS traffic:

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
# When asked "Command may disrupt existing ssh connections. Proceed with operation (y|n)?" type y
```

**Disconnect and reconnect as the new user** to verify everything works:

```bash
exit
```

Back in PowerShell on your PC:

```powershell
ssh lbzgiu@YOUR_SERVER_IP
```

You should be logged in as `lbzgiu`. You now have a secure server. From here, all commands run as `lbzgiu` (use `sudo` when a command needs admin rights).

---

## 3. Install dependencies

```bash
sudo apt update && sudo apt upgrade -y

# Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# PostgreSQL 16
sudo apt install -y postgresql postgresql-contrib

# Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server

# nginx + certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Git
sudo apt install -y git
```

---

## 4. PostgreSQL setup

```bash
sudo -u postgres psql <<EOF
CREATE USER lbzgiu WITH PASSWORD 'CHOOSE_A_STRONG_PASSWORD';
CREATE DATABASE squiidwiki_db OWNER lbzgiu;
CREATE DATABASE squiidwiki_test OWNER lbzgiu;
EOF
```

> `lbzgiu` is the general Postgres user for this server. Each project gets its own database.

---

## 5. Clone and configure the app

```bash
cd /home/lbzgiu
git clone https://github.com/YOUR_USERNAME/squiidwiki.git
cd squiidwiki
```

Create the `.env` file at the repo root:

```bash
cat > .env <<'EOF'
# Database
DATABASE_URL_PROD=postgresql+asyncpg://lbzgiu:YOUR_DB_PASSWORD@localhost:5432/squiidwiki_prod
DATABASE_URL_TEST=postgresql+asyncpg://lbzgiu:YOUR_DB_PASSWORD@localhost:5432/squiidwiki_test

# Auth — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=GENERATE_A_RANDOM_64_CHAR_HEX_STRING

# CORS — your domain (no trailing slash)
CORS_ORIGINS=["https://wiki.lbzgiu.xyz"]

# Environment
ENVIRONMENT=production

# Redis
REDIS_URL=redis://localhost:6379

# Cloudflare R2 — copy from your existing .env on Windows
R2_ENDPOINT_URL=https://2274e774b94707d729b8ca16df8c5fec.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=YOUR_R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY=YOUR_R2_SECRET_ACCESS_KEY
R2_BUCKET_PROD=squiidwiki-prod
R2_BUCKET_TEST=squiidwiki-prod
EOF
```

Generate the `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and replace GENERATE_A_RANDOM_64_CHAR_HEX_STRING in .env
nano .env
```

---

## 6. Backend setup

```bash
cd /home/lbzgiu/squiidwiki/backend

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # add uv to PATH for this session

# Create virtualenv and install deps
uv venv .venv
uv pip install -r requirements.txt

# Run migrations
.venv/bin/python -m alembic upgrade head
```

---

## 7. Frontend build

```bash
cd /home/lbzgiu/squiidwiki/frontend
npm ci
npm run build
# Output goes to frontend/dist/
```

The built static files are served by nginx directly — no Node.js process needed in production.

---

## 8. Systemd service for the backend

```bash
sudo nano /etc/systemd/system/squiidwiki.service
```

Paste:

```ini
[Unit]
Description=SquiidWiki API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=lbzgiu
WorkingDirectory=/home/lbzgiu/squiidwiki/backend
Environment=PATH=/home/lbzgiu/squiidwiki/backend/.venv/bin
ExecStart=/home/lbzgiu/squiidwiki/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+O`, Enter, then `Ctrl+X` to exit nano.

```bash
sudo systemctl daemon-reload
sudo systemctl enable squiidwiki
sudo systemctl start squiidwiki
sudo systemctl status squiidwiki   # should show "active (running)"
```

---

## 9. Point your domain at the server

In **Cloudflare DNS** for `lbzgiu.xyz`, add an **A record**:

| Type | Name | Content | Proxy status | TTL |
|---|---|---|---|---|
| A | `wiki` | `YOUR_SERVER_IP` | Proxied (orange cloud) | Auto |

DNS propagates instantly through Cloudflare.

---

## 10. nginx configuration

```bash
sudo nano /etc/nginx/sites-available/squiidwiki
```

Paste:

```nginx
server {
    listen 80;
    server_name wiki.lbzgiu.xyz;

    # Redirect HTTP → HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name wiki.lbzgiu.xyz;

    # SSL managed by certbot — populated automatically in step 11
    ssl_certificate /etc/letsencrypt/live/wiki.lbzgiu.xyz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wiki.lbzgiu.xyz/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Max upload size (photos)
    client_max_body_size 20M;

    # API — proxy to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend — serve built static files
    root /home/lbzgiu/squiidwiki/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/squiidwiki /etc/nginx/sites-enabled/
sudo nginx -t          # verify config — should say "syntax is ok"
sudo systemctl reload nginx
```

---

## 11. SSL certificate

```bash
sudo certbot --nginx -d wiki.lbzgiu.xyz
# Enter your email when asked
# Agree to terms (A)
# certbot auto-patches the nginx config with cert paths and sets up auto-renewal
```

Visit `https://wiki.lbzgiu.xyz` — you should see the app.

---

## 12. Create the first admin account

With the server running, hit the bootstrap endpoint once (only works when the `users` table is empty):

```bash
curl -s -X POST https://wiki.lbzgiu.xyz/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lbzgiu.xyz","password":"STRONG_PASSWORD","global_role":"ADMIN"}' | python3 -m json.tool
```

After that, all further accounts must be created through **Admin → Users → Add User** while logged in.

---

## 13. Deploying updates

```bash
cd /home/lbzgiu/squiidwiki

# Pull latest
git pull

# Backend — apply migrations + restart
cd backend
source .venv/bin/activate
python -m alembic upgrade head
sudo systemctl restart squiidwiki

# Frontend — rebuild
cd ../frontend
npm ci
npm run build

# nginx doesn't need restarting — it serves files from dist/ directly
```

---

## 14. Logs and monitoring

```bash
# Live API logs
sudo journalctl -u squiidwiki -f

# nginx access / error logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

---

## 15. Backups

Enable Hetzner's snapshot backup in the UI (server page → Backups → Enable, +20% of server cost). For database-level backups:

```bash
mkdir -p /home/lbzgiu/backups/squiidwiki
crontab -e
```

Add these two lines at the bottom (press `i` to insert if it opens in vim, `:wq` to save):

```
0 3 * * * pg_dump -U lbzgiu squiidwiki_db | gzip > /home/lbzgiu/backups/squiidwiki/squiidwiki_$(date +\%Y\%m\%d).sql.gz
0 4 * * * find /home/lbzgiu/backups/squiidwiki -name "*.sql.gz" -mtime +14 -delete
```

This dumps the database every night at 3 AM and keeps 14 days of history.

---

## Summary checklist

- [ ] `lbzgiu.xyz` purchased on Namecheap, pointed at Cloudflare nameservers
- [ ] SSH key generated on Windows (`ssh-keygen`)
- [ ] Hetzner account created, SSH key added, CX22 server `lbzgiu-vps` created
- [ ] Connected as `lbzgiu`, firewall configured
- [ ] System packages installed (Python, Node, Postgres, Redis, nginx)
- [ ] PostgreSQL user `lbzgiu` and databases `squiidwiki_db` / `squiidwiki_test` created
- [ ] Repo cloned to `/home/lbzgiu/squiidwiki/`, `.env` written with real secrets
- [ ] Backend virtualenv created, migrations run
- [ ] Frontend built (`npm run build`)
- [ ] systemd service `squiidwiki` enabled and running
- [ ] Cloudflare A record `wiki` → server IP added
- [ ] nginx config `squiidwiki` in place and tested (`nginx -t`)
- [ ] SSL cert issued for `wiki.lbzgiu.xyz` via certbot
- [ ] App loads at `https://wiki.lbzgiu.xyz`
- [ ] First admin account bootstrapped via curl
- [ ] Hetzner snapshot backups enabled + pg_dump cron set
