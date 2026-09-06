from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def send_success_email(reg: dict) -> None:
    to_addr = (reg.get("email") or "").strip()
    if not to_addr or "@" not in to_addr:
        raise ValueError("This registration has no valid email.")

    host = env("SMTP_HOST", "smtp.gmail.com")
    port = int(env("SMTP_PORT", "587") or "587")
    user = env("SMTP_USER")
    password = env("SMTP_PASS")
    from_email = env("FROM_EMAIL") or user
    from_name = env("FROM_NAME", "Pulse Heart Super Speciality Hospital")
    group = env("WHATSAPP_GROUP_URL")
    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASS are not set on the server.")
    if not group or "REPLACE_WITH" in group:
        raise ValueError("Set WHATSAPP_GROUP_URL in .env to the WhatsApp group invite link.")

    name = reg.get("name") or "Runner"
    msg = EmailMessage()
    msg["Subject"] = "You're in — Pulse Heart World Heart Day Run, 29 September"
    query_name = env("QUERY_NAME", "Dr. Kranthi Kumar")
    query_phone = env("QUERY_PHONE", "9949996644")
    query_email = env("QUERY_EMAIL", "kranthikumar@thepulseheart.com")
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_addr
    msg["Reply-To"] = f"{query_name} <{query_email}>"
    text = (
        f"Dear {name},\n\n"
        "Your payment for the Pulse Heart World Heart Day 5K/10K run is confirmed.\n\n"
        f"Distance: {reg.get('distance')}\n"
        f"T-shirt: {reg.get('tshirt')}\n"
        "Date: Tuesday, 29 September 2026\n"
        "Time: 6:00 am – 8:00 am\n"
        "Venue: Pulse Heart Super Speciality Hospital, Miyapur, Hyderabad\n\n"
        "Join the official WhatsApp group for reporting time, bib details, and updates:\n"
        f"{group}\n\n"
        "See you on 29 September.\n"
        "Pulse Heart Super Speciality Hospital\n"
        f"Queries: {query_name} · +91 {query_phone} · {query_email}\n"
    )
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;color:#222">
      <p>Dear {name},</p>
      <p>Your payment for the <strong>Pulse Heart World Heart Day 5K/10K run</strong> is confirmed.</p>
      <p>
        Distance: <strong>{reg.get('distance')}</strong><br>
        T-shirt: <strong>{reg.get('tshirt')}</strong><br>
        Date: <strong>Tuesday, 29 September 2026</strong><br>
        Time: <strong>6:00 am – 8:00 am</strong><br>
        Venue: Pulse Heart Super Speciality Hospital, Miyapur, Hyderabad
      </p>
      <p><a href="{group}" style="display:inline-block;background:#25D366;color:#fff;text-decoration:none;padding:12px 18px;border-radius:6px;font-weight:700">Join the WhatsApp group</a></p>
      <p style="font-size:13px;color:#555">If the button does not open, copy this link:<br>{group}</p>
      <p>See you on 29 September.<br>Pulse Heart Super Speciality Hospital<br>Queries: {query_name} · +91 {query_phone} · <a href="mailto:{query_email}">{query_email}</a></p>
    </div>
    """
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
