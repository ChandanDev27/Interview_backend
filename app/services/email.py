import os
from datetime import datetime, timedelta
from email.message import EmailMessage

import aiosmtplib
from email_validator import validate_email, EmailNotValidError
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

from app.database import get_database

# SMTP Configuration
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USERNAME)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# App info
APP_NAME = os.getenv("APP_NAME", "Interview Genie")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@example.com")

# Jinja2 setup for email templates
templates = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

# Logger setup
logger = logging.getLogger(__name__)

# Email validation
def is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False

# Resend limiter
async def can_resend_otp(email: str, limit: int = 3, window_minutes: int = 15) -> bool:
    db = await get_database()
    user = await db["users"].find_one({"email": email})

    if not user:
        return True  # allow if user doesn't exist yet

    last_sent = user.get("last_otp_sent")
    resend_count = user.get("otp_resend_count", 0)

    if last_sent:
        time_diff = datetime.utcnow() - last_sent
        if time_diff > timedelta(minutes=window_minutes):
            # reset window
            await db["users"].update_one(
                {"email": email},
                {"$set": {"otp_resend_count": 1, "last_otp_sent": datetime.utcnow()}}
            )
            return True
        elif resend_count >= limit:
            return False
        else:
            await db["users"].update_one(
                {"email": email},
                {
                    "$inc": {"otp_resend_count": 1},
                    "$set": {"last_otp_sent": datetime.utcnow()}
                }
            )
            return True
    else:
        await db["users"].update_one(
            {"email": email},
            {
                "$set": {
                    "otp_resend_count": 1,
                    "last_otp_sent": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True

# Send an email using SMTP with HTML template
async def send_email(email: str, subject: str, html_body: str) -> dict:
    if not is_valid_email(email):
        logger.error(f"Invalid email address: {email}")
        return {"error": "Invalid email address"}

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = email
        msg.set_content("This is an HTML email. Please use an HTML-compatible email viewer.")
        msg.add_alternative(html_body, subtype='html')

        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT) as server:
            await server.starttls()
            await server.login(SMTP_USERNAME, SMTP_PASSWORD)
            await server.send_message(msg)

        logger.info(f"Email sent successfully to {email} with subject '{subject}'")
        return {"message": "Email sent successfully!"}

    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP error while sending email to {email}: {str(e)}")
        return {"error": f"SMTP error occurred: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error while sending email to {email}: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

# OTP Email sender with template and limit checking
async def send_otp_email(email: str, user_name: str, otp: str) -> dict:
    can_send = await can_resend_otp(email)
    if not can_send:
        logger.warning(f"Too many OTP requests for {email}. Please try again later.")
        return {"error": "Too many OTP requests. Please try again later."}

    try:
        html = templates.get_template("emails/otp.html").render(
            user_name=user_name,
            otp=otp,
            app_name=APP_NAME,
            support_email=SUPPORT_EMAIL,
            year=datetime.utcnow().year
        )
        return await send_email(email, "Your OTP for Secure Access", html)
    except Exception as e:
        logger.error(f"Error rendering OTP email template: {str(e)}")
        return {"error": "Failed to generate OTP email content"}

# Welcome Email
async def send_welcome_email(email: str, user_name: str) -> dict:
    try:
        html = templates.get_template("emails/welcome.html").render(
            user_name=user_name,
            app_name=APP_NAME,
            support_email=SUPPORT_EMAIL,
            year=datetime.utcnow().year
        )
        return await send_email(email, f"Welcome to {APP_NAME}!", html)
    except Exception as e:
        logger.error(f"Error rendering welcome email template: {str(e)}")
        return {"error": "Failed to generate welcome email content"}

# Password Reset Email
async def send_password_reset_email(email: str, user_name: str, reset_link: str) -> dict:
    try:
        html = templates.get_template("emails/password_reset.html").render(
            user_name=user_name,
            reset_link=reset_link,
            app_name=APP_NAME,
            support_email=SUPPORT_EMAIL,
            year=datetime.utcnow().year
        )
        return await send_email(email, "Password Reset Instructions", html)
    except Exception as e:
        logger.error(f"Error rendering password reset email template: {str(e)}")
        return {"error": "Failed to generate password reset email content"}
