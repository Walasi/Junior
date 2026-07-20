import resend
from twilio.rest import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = settings.resend_api_key

# Initialize Twilio if keys provided
twilio_client = None
if settings.twilio_account_sid and settings.twilio_auth_token:
    twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

def send_email(to: str, subject: str, body: str):
    """Send email using Resend."""
    if not settings.resend_api_key:
        logger.warning("Resend API key missing, email not sent")
        return False
    try:
        resend.Emails.send(
            from_=settings.from_email,
            to=to,
            subject=subject,
            html=f"<p>{body}</p>"
        )
        logger.info(f"Email sent to {to}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False

def send_sms(to: str, body: str):
    """Send SMS using Twilio."""
    if not twilio_client:
        logger.warning("Twilio not configured, SMS not sent")
        return False
    try:
        message = twilio_client.messages.create(
            body=body,
            from_=settings.twilio_phone_number,
            to=to
        )
        logger.info(f"SMS sent to {to}, sid={message.sid}")
        return True
    except Exception as e:
        logger.error(f"SMS failed: {e}")
        return False

def alert_emergency_contacts(contacts, incident_type: str, user_name: str, location: str = None):
    """Send alerts to all emergency contacts."""
    subject = f"🚨 {incident_type.upper()} alert for {user_name}"
    body = f"{user_name} has reported an emergency: {incident_type}."
    if location:
        body += f" Location: {location}."
    body += " Please check on them immediately."

    for contact in contacts:
        if contact.email:
            send_email(contact.email, subject, body)
        if contact.phone:
            send_sms(contact.phone, body)