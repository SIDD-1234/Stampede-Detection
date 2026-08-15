from pydantic_settings import BaseSettings

class AlertSettings(BaseSettings):
    twilio_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_to_number: str = ""
    gmail_address: str = ""
    gmail_app_password: str = ""
    gmail_to: str = ""
    alerts_enabled: bool = True
    sms_enabled: bool = True
    email_enabled: bool = True

    class Config:
        env_file = ".env"

alert_settings = AlertSettings()