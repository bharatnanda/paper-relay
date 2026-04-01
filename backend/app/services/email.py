import os
import asyncio
import smtplib
from email.message import EmailMessage


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@paperrelay.app")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    async def send_magic_link(self, to_email: str, token: str) -> bool:
        """Send magic link email via SMTP or log it in development."""
        magic_link = f"{self.frontend_url.rstrip('/')}/login?token={token}"

        if not self.smtp_host:
            print(f"[DEV MODE] Magic link for {to_email}: {magic_link}")
            return True

        message = EmailMessage()
        message["Subject"] = "Your Magic Link to PaperRelay"
        message["From"] = self.from_email
        message["To"] = to_email
        message.set_content(
            "\n".join(
                [
                    "Welcome!",
                    "",
                    "Click the link below to sign in:",
                    magic_link,
                    "",
                    "This link expires in 24 hours.",
                    "If you didn't request this, ignore this email.",
                ]
            )
        )
        message.add_alternative(
            f"""
            <h1>Welcome!</h1>
            <p>Click the link below to sign in:</p>
            <p><a href="{magic_link}">{magic_link}</a></p>
            <p>This link expires in 24 hours.</p>
            <p>If you didn't request this, ignore this email.</p>
            """,
            subtype="html",
        )

        try:
            await asyncio.to_thread(self._send_message, message)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    def _send_message(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            if self.smtp_use_tls:
                smtp.starttls()
            if self.smtp_username:
                smtp.login(self.smtp_username, self.smtp_password or "")
            smtp.send_message(message)


email_service = EmailService()
