import smtplib
from email.mime.text import MIMEText
from app.core.config import settings


def send_admin_otp_email(to_email: str, otp_code: str) -> None:
    if not (settings.SMTP_USERNAME and settings.SMTP_PASSWORD and to_email):
        raise RuntimeError("SMTP settings are missing")

    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    subject = "Admin Login Verification Code"
    body = (
        "Your admin login verification code is:\n\n"
        f"{otp_code}\n\n"
        "This code expires in 5 minutes.\n"
        "If you did not request this, please secure your account immediately."
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(from_email, [to_email], msg.as_string())
