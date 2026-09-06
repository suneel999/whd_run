from __future__ import annotations

import io
import os
import secrets
import uuid
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

import qrcode
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from PIL import Image
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

import db
import mailer

load_dotenv()

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "uploads"
STATIC_QR = ROOT / "static" / "qr.png"
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 5 * 1024 * 1024

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.getenv("FLASK_SECRET", "pulse-run-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES
app.config["PREFERRED_URL_SCHEME"] = "https"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_event():
    return {
        "fee": env("FEE", "250"),
        "event_date": "29 September 2026",
        "event_time": "6:00 am – 8:00 am",
        "format_when": db.format_when,
        "TSHIRTS": db.TSHIRTS,
        "DISTANCES": db.DISTANCES,
        "query_name": "Dr. Kranthi Kumar",
        "query_phone": "9949996644",
        "query_email": "kranthikumar@thepulseheart.com",
    }


@app.get("/health")
def health():
    return {"ok": True, "service": "pulse-whd-run"}


@app.route("/", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        try:
            row = db.create(
                {
                    "token": secrets.token_urlsafe(16),
                    "name": request.form.get("name"),
                    "email": request.form.get("email"),
                    "phone": request.form.get("phone"),
                    "tshirt": request.form.get("tshirt"),
                    "distance": request.form.get("distance"),
                }
            )
        except ValueError as exc:
            flash(str(exc))
            return redirect("/")
        return redirect(f"/pay/{row['token']}")
    return render_template("register.html")


@app.route("/register", methods=["GET", "POST"])
def register_submit():
    if request.method == "GET":
        return redirect("/")
    return register_page()


@app.get("/pay/<token>")
def pay_page(token: str):
    row = db.get_by_token(token)
    if not row:
        abort(404)
    return render_template("pay.html", reg=row, has_qr=bool(env("UPI_ID") or STATIC_QR.exists()))


@app.post("/pay/<token>")
def pay_upload(token: str):
    row = db.get_by_token(token)
    if not row:
        abort(404)
    upload = request.files.get("screenshot")
    if not upload or not upload.filename:
        flash("Choose a payment screenshot to upload.")
        return redirect(url_for("pay_page", token=token))
    ext = Path(secure_filename(upload.filename)).suffix.lower()
    if ext not in ALLOWED_EXT:
        flash("Upload a JPG, PNG, or WEBP screenshot.")
        return redirect(url_for("pay_page", token=token))
    filename = f"{row['id']}_{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    upload.save(dest)
    try:
        with Image.open(dest) as img:
            img.verify()
    except Exception:
        dest.unlink(missing_ok=True)
        flash("That file does not look like an image. Try another screenshot.")
        return redirect(url_for("pay_page", token=token))
    db.save_screenshot(token, filename)
    return redirect(url_for("thanks_page", token=token))


@app.get("/thanks/<token>")
def thanks_page(token: str):
    row = db.get_by_token(token)
    if not row:
        abort(404)
    return render_template("thanks.html", reg=row)


@app.get("/qr.png")
def payment_qr():
    if STATIC_QR.exists():
        return send_file(STATIC_QR, mimetype="image/png")
    upi = env("UPI_ID")
    if not upi:
        abort(404)
    fee = env("FEE", "250")
    name = env("UPI_NAME", "Pulse Heart")
    query = urlencode({"pa": upi, "pn": name, "am": fee, "cu": "INR", "tn": "Pulse Heart WHD Run"})
    payload = f"upi://pay?{query}"
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_home"))
    error = ""
    if request.method == "POST":
        user = request.form.get("user", "")
        password = request.form.get("pass", "")
        admin_pass = env("ADMIN_PASS")
        if admin_pass and user == env("ADMIN_USER", "pulse") and password == admin_pass:
            session["admin"] = user
            return redirect(request.args.get("next") or url_for("admin_home"))
        error = "Wrong username or password."
    return render_template("admin_login.html", error=error)


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@login_required
def admin_home():
    status = request.args.get("status") or ""
    q = request.args.get("q") or ""
    return render_template(
        "admin.html",
        regs=db.list_regs(status, q),
        stats=db.stats(),
        status=status,
        q=q,
    )


@app.get("/admin/<int:reg_id>")
@login_required
def admin_detail(reg_id: int):
    row = db.get(reg_id)
    if not row:
        abort(404)
    return render_template("admin_detail.html", reg=row)


@app.post("/admin/<int:reg_id>/status")
@login_required
def admin_status(reg_id: int):
    status = (request.form.get("status") or "").strip()
    try:
        row = db.set_status(reg_id, status)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for("admin_detail", reg_id=reg_id))
    if status == "success":
        try:
            mailer.send_success_email(row)
            db.mark_email_sent(reg_id)
            flash("Marked success. Confirmation email sent with the WhatsApp group.")
        except Exception as exc:
            flash(f"Marked success, but email failed: {exc}")
    else:
        flash("Marked pending.")
    return redirect(url_for("admin_detail", reg_id=reg_id))


@app.post("/admin/<int:reg_id>/resend")
@login_required
def admin_resend(reg_id: int):
    row = db.get(reg_id)
    if not row:
        abort(404)
    try:
        mailer.send_success_email(row)
        db.mark_email_sent(reg_id)
        flash("Email sent again.")
    except Exception as exc:
        flash(str(exc))
    return redirect(url_for("admin_detail", reg_id=reg_id))


@app.get("/admin/shot/<int:reg_id>")
@login_required
def admin_shot(reg_id: int):
    row = db.get(reg_id)
    if not row or not row.get("screenshot"):
        abort(404)
    return send_from_directory(UPLOAD_DIR, row["screenshot"])


if __name__ == "__main__":
    db.connect()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
