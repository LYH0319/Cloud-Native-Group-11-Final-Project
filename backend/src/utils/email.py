import os
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send a password reset email, falling back to console output in local dev."""
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME") or "noreply@example.com"
    sender_name = os.getenv("SMTP_FROM_NAME")
    subject = "Job Scheduler password reset"
    body = (
        "A password reset was requested for your Job Scheduler account.\n\n"
        f"Reset your password here:\n{reset_link}\n\n"
        "If you did not request this, please ignore this email."
    )

    if not host:
        print(f"[password-reset-email] To: {to_email}")
        print(f"[password-reset-email] Link: {reset_link}")
        return

    message = EmailMessage()
    if sender_name and "@" in sender:
        local_part, domain = sender.rsplit("@", 1)
        message["From"] = Address(display_name=sender_name, username=local_part, domain=domain)
    else:
        message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
