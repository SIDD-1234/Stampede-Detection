import os
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def _bool_env(key, default="true"):
    return os.getenv(key, default).lower() == "true"

def send_sms_alert(message: str):
    if not (_bool_env("ALERTS_ENABLED") and _bool_env("SMS_ENABLED")):
        print("[ALERT] SMS skipped (disabled via .env)")
        return
    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_FROM_NUMBER"),
        to=os.getenv("TWILIO_TO_NUMBER"),
    )

def send_email_alert(subject: str, message: str):
    if not (_bool_env("ALERTS_ENABLED") and _bool_env("EMAIL_ENABLED")):
        print("[ALERT] Email skipped (disabled via .env)")
        return
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    to = os.getenv("GMAIL_TO")

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to, msg.as_string())