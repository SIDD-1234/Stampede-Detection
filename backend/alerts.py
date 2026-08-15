import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from alert_config import alert_settings

def send_sms_alert(message: str):
    if not (alert_settings.alerts_enabled and alert_settings.sms_enabled):
        print("[ALERT] SMS skipped (disabled via .env)")
        return
    client = Client(alert_settings.twilio_sid, alert_settings.twilio_auth_token)
    client.messages.create(
        body=message,
        from_=alert_settings.twilio_from_number,
        to=alert_settings.twilio_to_number,
    )

def send_email_alert(subject: str, message: str):
    if not (alert_settings.alerts_enabled and alert_settings.email_enabled):
        print("[ALERT] Email skipped (disabled via .env)")
        return
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = alert_settings.gmail_address
    msg["To"] = alert_settings.gmail_to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(alert_settings.gmail_address, alert_settings.gmail_app_password)
        server.sendmail(alert_settings.gmail_address, alert_settings.gmail_to, msg.as_string())