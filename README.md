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

## AWS deploy (same method as pulse-crm)

If the angiogram CRM already uses port 80 on this EC2, either use a second instance or change the port in `docker-compose.yml` to `"8081:8080"`.

1. Ubuntu EC2, open ports **22** and **80**
2. Install Docker:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

3. Copy this folder to `/opt/whd-run`
4. On the server:

```bash
cd /opt/whd-run
cp .env.example .env
nano .env
docker compose up -d --build
```

5. Public register: `http://YOUR-EC2-IP`  
   CRM: `http://YOUR-EC2-IP/admin/login`

Optional: point `run.thepulseheart.com` A-record to the EC2 IP, then add HTTPS later.

## Website note

On Hostinger, `run.html` and the homepage bar link to the run. After AWS is up, open `run.html` and change `REGISTER_URL` to your EC2 IP or `https://run.thepulseheart.com`.
