# Pulse Heart World Heart Day 5K/10K run

Separate app for the 29 September 2026 run (6:00–8:00 am).

- Public form: name, email, phone, 5K/10K, T-shirt size
- Then UPI QR for **₹250** and screenshot upload
- Staff CRM: all details + screenshots
- **Pending** or **Success**
- Success sends the runner an email with the WhatsApp group link

Copy this whole `whd-run` folder to AWS. Do not mix it into the Hostinger website files.

## What you fill in before going live

1. Copy `.env.example` to `.env`
2. Set a strong `ADMIN_PASS` and `FLASK_SECRET`
3. Put the Google Workspace app password in `SMTP_PASS` (same mailbox as website forms: `appointments@thepulseheart.com`)
4. Paste the WhatsApp group invite URL in `WHATSAPP_GROUP_URL`
5. Payment QR — one of these:
   - Set `UPI_ID` (example: `pulseheart@ybl`) and a QR is generated, or
   - Save your GPay/PhonePe QR image as `static/qr.png`

Staff login: `/admin/login`

## Local test

```bash
cd D:\pulse\whd-run
copy .env.example .env
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8080  
CRM: http://127.0.0.1:8080/admin/login

## AWS deploy (its own EC2)

1. Ubuntu EC2, open ports **22**, **80**, and **443**
2. On the server:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo git clone https://github.com/suneel999/whd_run.git /opt/whd-run
cd /opt/whd-run
sudo cp .env.example .env
sudo nano .env
sudo docker compose up -d --build
```

Set `PUBLIC_URL=https://event.thepulseheart.com` in `.env`.

Caddy in Docker serves the domain and gets a free HTTPS certificate. EC2 security group must allow **80** and **443**.

After you change files on GitHub, update the server with:

```bash
cd /opt/whd-run
sudo git pull
sudo docker compose up -d --build
```

## DNS: event.thepulseheart.com

In Hostinger DNS for `thepulseheart.com`:

| Type | Name | Value |
|---|---|---|
| A | `event` | the EC2 public IPv4 |

Wait 5–30 minutes. Then `http://event.thepulseheart.com` should open the form.

Staff CRM: `http://event.thepulseheart.com/admin/login`

The website Register button uses `https://event.thepulseheart.com`. After DNS works, add HTTPS (Let's Encrypt) so that link does not show a certificate warning.

## Website note

Homepage bar → `run.html` → `https://event.thepulseheart.com`. Upload `run.html` to Hostinger after you change it.
